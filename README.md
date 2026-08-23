# URL Shortener

[![CI](https://github.com/NarenNarayanan/url-shortener/actions/workflows/ci.yml/badge.svg)](https://github.com/NarenNarayanan/url-shortener/actions/workflows/ci.yml)

A URL shortener, built incrementally: FastAPI backend, React frontend, Postgres for storage, Redis for caching redirects and rate limiting.

## Stack

- **Backend:** FastAPI, SQLAlchemy 2.0, Alembic
- **DB:** PostgreSQL
- **Cache / rate limiting:** Redis
- **Auth:** JWT (HS256) + bcrypt
- **Frontend:** React + TypeScript, Vite, Tailwind CSS, shadcn/ui (Base UI), TanStack Query, React Hook Form + Zod, Recharts
- **Local dev:** Docker Compose — Postgres, Redis, Adminer, backend, frontend, all hot-reloading

## What's working right now

- User registration and login (JWT-based)
- URL shortening + redirect, with click tracking (count, last-clicked, IP/UA/referrer)
- Redis caching for redirects (cache-aside, TTL-based)
- Rate limiting on auth and URL creation endpoints (Redis-backed, survives multiple instances)
- URL management: list (pagination, search, sort), edit, delete — all owner-scoped
- Click analytics: daily/weekly time series, browser/OS/device breakdowns, top links
- Full frontend: landing page, auth pages, a dashboard (create/edit/delete links, copy-to-clipboard, QR codes), a per-link analytics page with charts, dark mode
- `/health` endpoint that actually checks Postgres/Redis connectivity instead of returning a hardcoded 200
- DB schema + Alembic migrations for `users`, `urls`, `clicks`
- Test suite (31 tests) running against a real Postgres + Redis, not mocks/SQLite

**🚀 Deployment:** Complete! See live demo below.

## Demo

**Live Application:** https://url-shortener-frontend-08cb.onrender.com/

## Running it locally

Needs Docker + Docker Compose.

```bash
docker compose up --build
```

`backend/.env` and `frontend/.env` are already committed (see "design decisions" below for why) — no need to copy them from the `.env.example` templates. Those templates exist for reference/first-time setup.

**Local URLs:**
- API: http://localhost:8000/docs
- Frontend: http://localhost:5173
- Adminer (DB browser): http://localhost:8080 — server `postgres`, user/pass `postgres`/`postgres`, database `urlshortener`

Migrations aren't run automatically on container start (see "why" below), so after the containers are up:

```bash
docker compose exec backend alembic upgrade head
```

## Running tests

```bash
docker compose exec backend pytest -v
```

Tests run against a real Postgres database (`urlshortener_test`) and a dedicated Redis logical database (DB 1, vs. the app's normal DB 0), both created/isolated automatically. Each test runs inside a SAVEPOINT that rolls back afterward, so they're fast and don't interfere with each other.

## Project structure

```
.github/workflows/  # CI — runs backend tests + frontend typecheck/lint/build on every push/PR
backend/
  app/
    routers/       # HTTP layer only — request/response shape, no business logic
    services/      # business logic, called by routers
    models/        # SQLAlchemy models
    schemas/        # Pydantic request/response models
    auth/           # password hashing, JWT, get_current_user dependency
    utils/          # shared exceptions, helpers, short code + UA parsing
    rate_limit.py   # slowapi limiter (Redis-backed)
    config.py       # settings, read from environment variables
    database.py     # SQLAlchemy engine/session setup
    cache.py        # Redis client
  alembic/          # DB migrations
  db/init/          # Postgres init scripts (creates the test DB)
  tests/
frontend/
  src/
    pages/          # route-level components (Landing, Login, Register, Dashboard, Analytics)
    components/     # reusable components; components/ui is shadcn-managed
    contexts/       # AuthContext (token + current user)
    hooks/          # small reusable hooks (e.g. debounced search input)
    lib/            # API client, typed endpoint functions, validation schemas
    types/          # TypeScript types mirroring backend Pydantic schemas
docker-compose.yml
```

## API so far

| Method | Path                       | Auth | Description                          |
|--------|-----------------------------|------|---------------------------------------|
| POST   | /register                   | no   | create an account (rate limited)      |
| POST   | /login                      | no   | get a JWT access token (rate limited) |
| GET    | /me                          | yes  | current user's info                   |
| POST   | /urls                       | yes  | create a short link (rate limited)    |
| GET    | /urls                       | yes  | list your links (pagination/search/sort) |
| PATCH  | /urls/{short_code}           | yes  | edit a link's destination/expiration  |
| DELETE | /urls/{short_code}           | yes  | delete a link                         |
| GET    | /urls/{short_code}/analytics | yes  | click analytics for a link            |
| GET    | /{short_code}                | no   | redirect to the original URL          |
| GET    | /health                     | no   | Postgres + Redis connectivity check   |

Full interactive docs (Swagger) at `/docs` once the backend is running.

## A few design decisions worth explaining

**`.env` files are committed, not gitignored.** Unusual, and deliberate: there's no shared secrets manager for this project, so the committed `.env` files (with placeholder, non-sensitive values) let you run `docker compose up` without any setup. In production, environment variables would override these.

**Login takes a JSON body, not FastAPI's OAuth2 form-login flow.** The frontend is a JSON API client, so a form-encoded login endpoint would be the odd one out. You lose Swagger's auto-filled OAuth2 flow, but gain a consistent API shape.

**Login returns the same error whether the email doesn't exist or the password is wrong** — and editing/deleting someone else's link returns the same 404 as a link that doesn't exist at all. Disclosing *why* an auth attempt failed is a security anti-pattern. The frontend handles all the UX gracefully.

**Migrations run manually**, not on container startup. Auto-migrating on boot is convenient with one instance and breaks the moment you run more than one — multiple containers racing to migrate either lock or collide. `alembic upgrade head` is explicit and safe.

**`is_expired` on a URL is computed, not stored as a column.** It's just `now() > expires_at`. No background job has to run to keep a status flag in sync.

**`click_count` and `last_clicked_at` are denormalized onto the `urls` table**, updated atomically alongside each click insert, so the dashboard doesn't have to `COUNT()`/`MAX()` the clicks table on every page load.

**Redirects are cached in Redis (cache-aside), not just the DB.** A redirect first checks Redis for `short_code -> {id, original_url, expires_at}`; on a miss it falls back to Postgres and populates the cache. TTL is 24 hours.

**Rate limiting is Redis-backed, not in-memory**, so the limit holds across multiple backend instances instead of each one enforcing its own separate quota. `/register` and `/login` are capped at 10 requests per minute per IP.

**Browser/OS/device are parsed from `user_agent` once, at write time**, not re-parsed on every analytics query.

**Constraint names are explicit** (`pk_users`, `fk_urls_user_id_users`, etc.) via a naming convention on the SQLAlchemy metadata, set up before the first migration existed. Without this, Postgres would generate opaque names, and diffs become unreadable.

**Tests use a real Postgres DB with a SAVEPOINT-per-test rollback pattern, and a dedicated Redis logical database**, not mocks. The `Click` model uses a Postgres-specific `INET` column for IP addresses.

**The frontend uses Base UI (via shadcn/ui's "base" preset), not Radix** — composition uses a `render` prop (`<Button render={<Link to="/" />}>`) rather than Radix's `asChild`. Token storage is in memory (not localStorage), so it's cleared on page reload — no stale token bugs.

## Roadmap

- [x] Project scaffolding, Docker Compose, health check
- [x] DB models + Alembic migrations
- [x] Auth (register / login / JWT)
- [x] URL shortening + redirect
- [x] Redis caching for redirects
- [x] Rate limiting (slowapi)
- [x] URL management — list with pagination/search/sort, edit, delete
- [x] Click analytics — daily/weekly breakdown, top links, browser/OS/device parsing
- [x] Frontend: auth pages, dashboard, analytics page, QR codes, copy button
- [x] CI (GitHub Actions)
- [x] **Deployment (Render)** — 🚀 Complete
