FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-dev

COPY ./app ./app

ENV PATH="/app/.venv/bin:$PATH"

CMD ["taskiq", "worker", "app.core.broker:broker", "--fs-discover", "--workers", "1"]