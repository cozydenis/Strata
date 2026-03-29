FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (layer-cached)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy source
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini ./

EXPOSE 8000

# Run DB migrations then start the server
# Railway injects $PORT; fall back to 8000 for local docker run
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn strata_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
