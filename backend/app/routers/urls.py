from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import settings
from app.database import get_db
from app.models import User
from app.rate_limit import limiter
from app.schemas.url import URLCreate, URLOut
from app.services import url_service

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
