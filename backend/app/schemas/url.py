from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.models.url import URL


class URLCreate(BaseModel):
    original_url: HttpUrl
    expires_at: datetime | None = None


class URLOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    short_code: str
    short_url: str
    original_url: str
    created_at: datetime
    expires_at: datetime | None
    click_count: int
    last_clicked_at: datetime | None
    is_expired: bool

    @classmethod
    def from_model(cls, url: URL, base_redirect_url: str) -> "URLOut":
        return cls(
            id=url.id,
            short_code=url.short_code,
            short_url=f"{base_redirect_url}/{url.short_code}",
            original_url=url.original_url,
            created_at=url.created_at,
            expires_at=url.expires_at,
            click_count=url.click_count,
            last_clicked_at=url.last_clicked_at,
            is_expired=url.is_expired,
        )
