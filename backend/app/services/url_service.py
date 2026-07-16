"""
URL shortening business logic. No FastAPI imports, same reasoning as
auth_service.py: unit-testable on its own, routers translate these
exceptions into HTTP responses.
"""
import json
from dataclasses import dataclass
from datetime import datetime, timezone

from redis import Redis
from sqlalchemy.orm import Session

from app.models import URL, Click, User
from app.schemas.url import URLCreate
from app.utils.exceptions import URLExpiredError, URLNotFoundError
from app.utils.short_code import generate_short_code

MAX_SHORT_CODE_ATTEMPTS = 5
CACHE_KEY_PREFIX = "url:short_code:"


@dataclass
class ResolvedURL:
    """
    What a redirect actually needs — deliberately not the full URL model, so
    a cache hit can satisfy a redirect without ever touching Postgres.
    """
    id: int
    original_url: str


def _cache_key(short_code: str) -> str:
    return f"{CACHE_KEY_PREFIX}{short_code}"


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


def get_active_url_by_code(db: Session, redis_client: Redis, short_code: str, cache_ttl_seconds: int) -> ResolvedURL:
    cached = redis_client.get(_cache_key(short_code))
    if cached is not None:
        data = json.loads(cached)
        if data["expires_at"] is not None and datetime.fromisoformat(data["expires_at"]) < datetime.now(timezone.utc):
            raise URLExpiredError(short_code)
        return ResolvedURL(id=data["id"], original_url=data["original_url"])

    url = db.query(URL).filter(URL.short_code == short_code).first()
    if url is None:
        raise URLNotFoundError(short_code)
    if url.is_expired:
        raise URLExpiredError(short_code)

    redis_client.set(
        _cache_key(short_code),
        json.dumps({
            "id": url.id,
            "original_url": url.original_url,
            "expires_at": url.expires_at.isoformat() if url.expires_at else None,
        }),
        ex=cache_ttl_seconds,
    )
    return ResolvedURL(id=url.id, original_url=url.original_url)


def record_click(db: Session, url_id: int, ip_address: str | None, user_agent: str | None, referrer: str | None) -> None:
    db.add(Click(url_id=url_id, ip_address=ip_address, user_agent=user_agent, referrer=referrer))
    # Atomic increment via SQL expression (read-modify-write in Python would
    # race under concurrent redirects) — see URL model notes.
    db.query(URL).filter(URL.id == url_id).update({
        "click_count": URL.click_count + 1,
        "last_clicked_at": datetime.now(timezone.utc),
    })
    db.commit()
