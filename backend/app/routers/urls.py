from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from redis import Redis
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.cache import get_redis
from app.config import settings
from app.database import get_db
from app.models import User
from app.rate_limit import limiter
from app.schemas.url import URLCreate, URLListResponse, URLOut, URLUpdate
from app.services import url_service
from app.utils.exceptions import URLNotFoundError

router = APIRouter(tags=["urls"])


@router.post("/urls", response_model=URLOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_url(
    request: Request,
    url_in: URLCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> URLOut:
    url = url_service.create_short_url(db, current_user, url_in, settings.short_code_length)
    return URLOut.from_model(url, settings.base_redirect_url)


@router.get("/urls", response_model=URLListResponse)
def list_urls(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    sort_by: Literal["created_at", "click_count"] = Query("created_at"),
    order: Literal["asc", "desc"] = Query("desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> URLListResponse:
    items, total = url_service.list_urls_for_owner(db, current_user, page, page_size, search, sort_by, order)
    return URLListResponse(
        items=[URLOut.from_model(url, settings.base_redirect_url) for url in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/urls/{short_code}", response_model=URLOut)
def update_url(
    short_code: str,
    url_in: URLUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> URLOut:
    try:
        url = url_service.update_url(db, redis_client, current_user, short_code, url_in)
    except URLNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Short link not found")
    return URLOut.from_model(url, settings.base_redirect_url)


@router.delete("/urls/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_url(
    short_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> None:
    try:
        url_service.delete_url(db, redis_client, current_user, short_code)
    except URLNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Short link not found")
