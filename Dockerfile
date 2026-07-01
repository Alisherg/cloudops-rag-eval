FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9.17 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --frozen --no-dev

FROM python:3.12-slim

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    CHROMA_PATH=/tmp/cloudops-rag-eval/chroma

COPY --from=builder /app/.venv /app/.venv
COPY src ./src
COPY docs ./docs

EXPOSE 8080

CMD ["uvicorn", "cloudops_rag_eval.main:app", "--host", "0.0.0.0", "--port", "8080"]
