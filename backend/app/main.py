"""
Application entrypoint.

Keep this file thin: create the app, wire up middleware/logging, and
include routers. All actual logic lives in routers/services/models.
"""
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.rate_limit import limiter
from app.routers import analytics, auth, health, redirect, urls

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting %s in '%s' mode", settings.app_name, settings.environment)
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description="A production-style URL shortener API.",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_URL = "https://url-shortener-frontend-08cb.onrender.com/"


@app.get("/", include_in_schema=False)
def root() -> HTMLResponse:
    return HTMLResponse(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>{settings.app_name}</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 640px; margin: 4rem auto; padding: 0 1rem; color: #1a1a1a; }}
  h1 {{ font-size: 1.5rem; }}
  a {{ color: #2563eb; }}
  code {{ background: #f1f5f9; padding: 0.15rem 0.4rem; border-radius: 4px; }}
</style>
</head>
<body>
  <h1>{settings.app_name}</h1>
  <p>Backend API for a full-stack URL shortener: FastAPI + PostgreSQL + Redis, with
  user accounts, click analytics, and rate limiting.</p>
  <p>
    <a href="{FRONTEND_URL}">Open the app</a>
    &nbsp;&middot;&nbsp;
    <a href="/docs">API docs</a>
    &nbsp;&middot;&nbsp;
    <a href="/health">Health check</a>
  </p>
  <p>Short links created in the app look like <code>/AbCd123</code> and redirect from this domain.</p>
</body>
</html>""")


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(urls.router)
app.include_router(analytics.router)

app.include_router(redirect.router)  # MUST be included LAST — see routers/redirect.py note on route ordering
