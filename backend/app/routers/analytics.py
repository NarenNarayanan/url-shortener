from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.analytics import URLAnalytics
from app.services import url_service
from app.utils.exceptions import URLNotFoundError

router = APIRouter(tags=["analytics"])


@router.get("/urls/{short_code}/analytics", response_model=URLAnalytics)
def get_url_analytics(
    short_code: str,
    days: int = Query(30, ge=1, le=365),
    group_by: Literal["day", "week"] = Query("day"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> URLAnalytics:
    try:
        data = url_service.get_url_analytics(db, current_user, short_code, days, group_by)
    except URLNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Short link not found")
    return URLAnalytics(**data)
