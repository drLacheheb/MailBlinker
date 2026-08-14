FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=0 \
    UV_LINK_MODE=copy \
    PORT=8000 \
    HOST=0.0.0.0

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -u 10001 -m -s /bin/sh appuser \
    && mkdir -p /app/data /app/logs \
    && chown -R appuser:appuser /app

COPY pyproject.toml ./
COPY packages/ ./packages/
COPY services/ ./services/

RUN uv sync --no-cache

COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY run.py ./

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["sh", "-c", "uv run alembic upgrade head && uv run python run.py"]
