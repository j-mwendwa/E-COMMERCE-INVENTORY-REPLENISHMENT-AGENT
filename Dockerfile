# ─────────────────────────────────────────────────────────────────────────────
# INVENTORY-REPLENISHMENT-AGENT — Multi-Stage Dockerfile
#
# Stages:
#   1. builder     — installs Python packages + pre-caches embedding model
#   2. runtime     — lean production image  (default build target)
#   3. dev         — development image with hot-reload (not for production)
#
# Build examples:
#   docker build --target runtime -t inventory-replenishment-agent:latest .
#   docker build --target dev     -t inventory-replenishment-agent:dev    .
# ─────────────────────────────────────────────────────────────────────────────

ARG PYTHON_VERSION=3.11

# ══════════════════════════════════════════════════════════════════════════════
# Stage 1 — builder: install Python deps + pre-cache embedding model
# ══════════════════════════════════════════════════════════════════════════════
FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build-time system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gcc \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy packaging metadata + source first (layer-cache friendly)
COPY pyproject.toml ./
COPY src/       ./src/
COPY configs/   ./configs/
COPY prompts/   ./prompts/

# Install into system Python so every subsequent RUN can import
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -e ".[dev]"

# Pre-download embedding model — non-fatal so CI build succeeds even if
# HuggingFace Hub is unreachable or the model download is slow
ENV HF_HOME=/app/.cache/huggingface
RUN python3 -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('BAAI/bge-small-en-v1.5'); \
print('Embedding model cached.')" \
    || echo "⚠️  Model pre-cache skipped (will download on first request)"

# ══════════════════════════════════════════════════════════════════════════════
# Stage 2 — runtime: lean production image  (default build target)
# ══════════════════════════════════════════════════════════════════════════════
FROM python:${PYTHON_VERSION}-slim AS runtime

ARG APP_USER=appuser
ARG APP_UID=1001

LABEL org.opencontainers.image.title="INVENTORY REPLENISHMENT AGENT API" \
      org.opencontainers.image.description="Automated e-commerce inventory replenishment agent with predictive demand, supplier selection, and human-in-the-loop escalation" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.cache/huggingface

# Runtime system deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy pre-cached model (may be empty if download was skipped — that's fine)
COPY --from=builder /app/.cache /app/.cache

# Copy application source
COPY src/       ./src/
COPY configs/   ./configs/
COPY prompts/   ./prompts/
COPY pyproject.toml ./

# Persistent data dirs
RUN mkdir -p data/checkpoints data/memory data/uploads

# Non-root user
RUN groupadd --gid ${APP_UID} ${APP_USER} \
    && useradd --uid ${APP_UID} --gid ${APP_UID} \
               --shell /bin/bash --create-home ${APP_USER} \
    && chown -R ${APP_USER}:${APP_USER} /app

USER ${APP_USER}

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

CMD uvicorn src.api.main:app \
     --host 0.0.0.0 \
     --port ${PORT:-8000} \
     --workers 1 \
     --access-log \
     --proxy-headers \
     --forwarded-allow-ips "*"

# ══════════════════════════════════════════════════════════════════════════════
# Stage 3 — dev: hot-reload development image (not for production)
# ══════════════════════════════════════════════════════════════════════════════
FROM builder AS dev

LABEL org.opencontainers.image.title="INVENTORY REPLENISHMENT AGENT Dev" \
      org.opencontainers.image.description="Development image with hot-reload"

WORKDIR /app

COPY . .

RUN pip install -e ".[dev,eval]"

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload"]
