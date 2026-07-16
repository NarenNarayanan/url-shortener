"""
URL shortening business logic. No FastAPI imports, same reasoning as
auth_service.py: unit-testable on its own, routers translate these
exceptions into HTTP responses.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import URL, Click, User
from app.schemas.url import URLCreate
from app.utils.exceptions import URLExpiredError, URLNotFoundError
from app.utils.short_code import generate_short_code

MAX_SHORT_CODE_ATTEMPTS = 5


def create_short_url(db: Session, owner: User, url_in: URLCreate, short_code_length: int) -> URL:
    # Collisions are astronomically unlikely at this alphabet/length, but we
    # check rather than assume — a silent overwrite of someone else's short
    # code would be a bad bug to have.
    for _ in range(MAX_SHORT_CODE_ATTEMPTS):
        code = generate_short_code(short_code_length)
        if not db.query(URL).filter(URL.short_code == code).first():
            break
    else:
        raise RuntimeError("Could not generate a unique short code after several attempts")

    url = URL(
        short_code=code,
        original_url=str(url_in.original_url),
        user_id=owner.id,
        expires_at=url_in.expires_at,
    )
    db.add(url)
    db.commit()
    db.refresh(url)
    return url


def get_active_url_by_code(db: Session, short_code: str) -> URL:
    url = db.query(URL).filter(URL.short_code == short_code).first()
    if url is None:
        raise URLNotFoundError(short_code)
    if url.is_expired:
        raise URLExpiredError(short_code)
    return url


def record_click(db: Session, url: URL, ip_address: str | None, user_agent: str | None, referrer: str | None) -> None:
    db.add(Click(url_id=url.id, ip_address=ip_address, user_agent=user_agent, referrer=referrer))
    # Atomic increment via SQL expression (url.click_count += 1 would be a
    # read-modify-write race under concurrent redirects) — see URL model notes.
    url.click_count = URL.click_count + 1
    url.last_clicked_at = datetime.now(timezone.utc)
    db.commit()
