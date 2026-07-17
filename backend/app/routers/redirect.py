"""
NOTE on route ordering: GET /{short_code} is a catch-all — Starlette
matches routes in registration order, not by specificity, so this router
MUST be included in main.py AFTER every other router. If it were included
first, a request for e.g. GET /me would match here instead, with
short_code="me".
"""
import ipaddress

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from redis import Redis
from sqlalchemy.orm import Session

from app.cache import get_redis
from app.config import settings
from app.database import get_db, get_session_factory
from app.rate_limit import limiter
from app.services import url_service
from app.utils.exceptions import URLExpiredError, URLNotFoundError

router = APIRouter(tags=["redirect"])


def _client_ip(request: Request) -> str | None:
    if request.client is None:
        return None
    # The `clicks.ip_address` column is Postgres INET, which rejects anything
    # that isn't a real IP (e.g. "testclient" from FastAPI's TestClient, or
    # unusual values some reverse proxies can pass through).
    try:
        ipaddress.ip_address(request.client.host)
    except ValueError:
        return None
    return request.client.host


@router.get("/{short_code}")
@limiter.limit("100/second")
def redirect_to_original(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
    session_factory=Depends(get_session_factory),
) -> RedirectResponse:
    try:
        resolved = url_service.get_active_url_by_code(
            db, redis_client, short_code, settings.redis_cache_ttl_seconds
        )
    except URLNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Short link not found")
    except URLExpiredError:
        raise HTTPException(status.HTTP_410_GONE, detail="Short link has expired")

    # Backgrounded so the click write (a Click insert + click_count update)
    # never adds latency to the redirect itself — this is the hottest path
    # in the app, and the click record is a best-effort side effect, not
    # something the visitor should wait on.
    background_tasks.add_task(
        url_service.record_click_background,
        session_factory,
        resolved.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
    )
    return RedirectResponse(url=resolved.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
