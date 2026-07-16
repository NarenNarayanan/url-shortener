FROM python:3.12-slim AS base

WORKDIR /app

# System deps needed to build psycopg2 and bcrypt from source if wheels are unavailable
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# --- dev: adds test tooling (pytest, httpx) on top of base. Used by docker-compose.yml. ---
FROM base AS dev

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# --reload watches for file changes; the source is bind-mounted in docker-compose.yml
# so edits on the host are picked up immediately without rebuilding the image.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- prod: base only, no test tooling, no --reload. Target for real deployments. ---
FROM base AS prod

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
