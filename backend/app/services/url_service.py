"""
URL shortening business logic. No FastAPI imports, same reasoning as
auth_service.py: unit-testable on its own, routers translate these
exceptions into HTTP responses.
"""
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from redis import Redis
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import URL, Click, User
from app.schemas.url import URLCreate, URLUpdate
from app.utils.exceptions import URLExpiredError, URLNotFoundError
from app.utils.short_code import generate_short_code
from app.utils.user_agent import parse_user_agent

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
    browser, os_name, device_type = parse_user_agent(user_agent)
    db.add(Click(
        url_id=url_id,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer,
        browser=browser,
        os=os_name,
        device_type=device_type,
    ))
    # Atomic increment via SQL expression (read-modify-write in Python would
    # race under concurrent redirects) — see URL model notes.
    db.query(URL).filter(URL.id == url_id).update({
        "click_count": URL.click_count + 1,
        "last_clicked_at": datetime.now(timezone.utc),
    })
    db.commit()


def _get_owned_url(db: Session, owner: User, short_code: str) -> URL:
    # Same 404 whether the code doesn't exist or belongs to someone else —
    # confirming "this code exists but isn't yours" would leak information
    # about other users' links, same reasoning as login's generic error.
    url = db.query(URL).filter(URL.short_code == short_code, URL.user_id == owner.id).first()
    if url is None:
        raise URLNotFoundError(short_code)
    return url


def list_urls_for_owner(
    db: Session,
    owner: User,
    page: int,
    page_size: int,
    search: str | None,
    sort_by: Literal["created_at", "click_count"],
    order: Literal["asc", "desc"],
) -> tuple[list[URL], int]:
    query = db.query(URL).filter(URL.user_id == owner.id)
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(URL.original_url.ilike(pattern), URL.short_code.ilike(pattern)))

    total = query.count()

    sort_column = URL.created_at if sort_by == "created_at" else URL.click_count
    query = query.order_by(sort_column.desc() if order == "desc" else sort_column.asc())

    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def update_url(db: Session, redis_client: Redis, owner: User, short_code: str, url_in: URLUpdate) -> URL:
    url = _get_owned_url(db, owner, short_code)

    if url_in.original_url is not None:
        url.original_url = str(url_in.original_url)
    if "expires_at" in url_in.model_fields_set:
        url.expires_at = url_in.expires_at

    db.commit()
    db.refresh(url)
    # Without this, a stale cached destination (or expiry) could keep being
    # served for up to redis_cache_ttl_seconds after the edit.
    redis_client.delete(_cache_key(short_code))
    return url


def delete_url(db: Session, redis_client: Redis, owner: User, short_code: str) -> None:
    url = _get_owned_url(db, owner, short_code)
    db.delete(url)
    db.commit()
    redis_client.delete(_cache_key(short_code))


def _breakdown(db: Session, url_id: int, column) -> list[dict]:
    rows = (
        db.query(column.label("label"), func.count().label("count"))
        .filter(Click.url_id == url_id)
        .group_by(column)
        .order_by(func.count().desc())
        .all()
    )
    return [{"label": row.label or "unknown", "count": row.count} for row in rows]


def get_url_analytics(
    db: Session,
    owner: User,
    short_code: str,
    days: int,
    group_by: Literal["day", "week"],
) -> dict:
    url = _get_owned_url(db, owner, short_code)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    period = func.date_trunc(group_by, Click.timestamp)
    time_series_rows = (
        db.query(period.label("period"), func.count().label("count"))
        .filter(Click.url_id == url.id, Click.timestamp >= since)
        .group_by("period")
        .order_by("period")
        .all()
    )

    return {
        "short_code": url.short_code,
        "total_clicks": url.click_count,
        "group_by": group_by,
        "clicks_over_time": [{"period": row.period, "count": row.count} for row in time_series_rows],
        "by_browser": _breakdown(db, url.id, Click.browser),
        "by_os": _breakdown(db, url.id, Click.os),
        "by_device_type": _breakdown(db, url.id, Click.device_type),
    }
