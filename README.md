# URL Shortener

A URL shortener, built incrementally: FastAPI backend, React frontend, Postgres for storage, Redis for caching redirects. Being built in stages, each one runnable on its own — see the roadmap below for what's done and what's not.

## Stack

- **Backend:** FastAPI, SQLAlchemy 2.0, Alembic
- **DB:** PostgreSQL
- **Cache:** Redis
- **Auth:** JWT (HS256) + bcrypt
- **Frontend:** React (Vite)
- **Local dev:** Docker Compose — Postgres, Redis, Adminer, backend, frontend, all hot-reloading

## What's working right now

- User registration and login (JWT-based)
- `/health` endpoint that actually checks Postgres/Redis connectivity instead of returning a hardcoded 200
- DB schema + Alembic migrations for `users`, `urls`, `clicks`
- Auth test suite (9 tests) running against a real Postgres database, not SQLite

Not built yet: URL shortening/redirects, caching, rate limiting, analytics, the actual frontend UI. See the roadmap at the bottom.

## Running it locally

Needs Docker + Docker Compose.

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```

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

Tests run against a real Postgres database (`urlshortener_test`), created automatically the first time the `postgres` container initializes (see `backend/db/init/01-create-test-db.sql`). Each test runs inside its own transaction that gets rolled back afterward, so nothing persists between runs — you can run the suite as many times as you want without cleaning up manually.

## Project structure

```
backend/
  app/
    routers/       # HTTP layer only — request/response shape, no business logic
    services/      # business logic, called by routers
    models/        # SQLAlchemy models
    schemas/        # Pydantic request/response models
    auth/           # password hashing, JWT, get_current_user dependency
    utils/          # shared exceptions, helpers
    config.py       # settings, read from environment variables
    database.py     # SQLAlchemy engine/session setup
    cache.py        # Redis client
  alembic/          # DB migrations
  db/init/          # Postgres init scripts (creates the test DB)
  tests/
frontend/
  src/
docker-compose.yml
```

## API so far

| Method | Path      | Auth | Description                       |
|--------|-----------|------|------------------------------------|
| POST   | /register | no   | create an account                  |
| POST   | /login    | no   | get a JWT access token             |
| GET    | /me       | yes  | current user's info                |
| GET    | /health   | no   | Postgres + Redis connectivity check |

Full interactive docs (Swagger) at `/docs` once the backend is running.

## A few design decisions worth explaining

**Login takes a JSON body, not FastAPI's OAuth2 form-login flow.** The frontend is a JSON API client, so a form-encoded login endpoint would be the odd one out. You lose Swagger's auto-filled OAuth2 "Authorize" flow, but you can still paste a bearer token into Swagger's Authorize dialog directly.

**Login returns the same error whether the email doesn't exist or the password is wrong.** Distinguishing them would let someone enumerate which emails are registered.

**Migrations run manually**, not on container startup. Auto-migrating on boot is convenient with one instance and breaks the moment you run more than one — multiple containers racing to migrate at once, or new code briefly running against an old schema mid-deploy.

**`is_expired` on a URL is computed, not stored as a column.** It's just `now() > expires_at`. No background job has to run to keep a status flag in sync.

**`click_count` and `last_clicked_at` are denormalized onto the `urls` table**, updated alongside each click insert, so the dashboard doesn't have to `COUNT()`/`MAX()` the clicks table for every row on every page load.

**Constraint names are explicit** (`pk_users`, `fk_urls_user_id_users`, etc.) via a naming convention on the SQLAlchemy metadata, set up before the first migration existed. Without this, Postgres autogenerates constraint names and Alembic can't reliably generate a migration to drop one later.

**Tests use a real Postgres DB with a SAVEPOINT-per-test rollback pattern**, not SQLite. The `Click` model uses a Postgres-specific `INET` column for IP addresses, so SQLite isn't a faithful stand-in anyway — better to catch Postgres-specific issues in tests than the first time it runs in Docker.

## Roadmap

- [x] Project scaffolding, Docker Compose, health check
- [x] DB models + Alembic migrations
- [x] Auth (register / login / JWT)
- [ ] URL shortening + redirect
- [ ] Redis caching for redirects
- [ ] Rate limiting (slowapi)
- [ ] URL management — list with pagination/search/sort, edit, delete
- [ ] Click analytics — daily/weekly breakdown, top links, browser/OS/device parsing
- [ ] Frontend: auth pages, dashboard, analytics page, QR codes, copy button
- [ ] CI (GitHub Actions)
- [ ] Deployment (Render/Fly.io)
