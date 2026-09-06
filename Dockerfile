FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

COPY . .

CMD ["sh", "-c", "exec /app/.venv/bin/uvicorn app.api:app --host 0.0.0.0 --port ${PORT:-8080}"]