# syntax=docker/dockerfile:1
#
# QPilot — Multi-stage Docker image
# ===================================
#
# Builder stage
#   Installs all Python dependencies (production only) under --prefix=/install.
#   A minimal stub package is created so pip resolves the project's pyproject.toml
#   without needing the full application source.  This separates dependency layer
#   caching from application layer caching.
#
# Runtime stage
#   Copies only the installed packages from the builder and the application source
#   code.  Runs as non-root user "qpilot".  Starts uvicorn with exec-form so that
#   Docker signals (SIGTERM) reach uvicorn directly.
#
# Usage (development)
#   docker compose up --build
#
# Usage (production build)
#   docker build -t qpilot:latest .
#   docker run --rm -p 8000:8000 qpilot:latest

# ═══════════════════════════════════════════════════════════════════════════════
# Stage 1 — Builder
# ═══════════════════════════════════════════════════════════════════════════════
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system build dependencies needed for native Python extensions.
# These are NOT carried into the runtime stage.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ── Layer 1: Python dependencies ─────────────────────────────
# Copy only the dependency specification so that Docker layer caching
# keeps this layer valid across source-code changes.
COPY pyproject.toml .

# Create a minimal stub package so pip can resolve the project's
# pyproject.toml without needing the full app/ directory.
RUN mkdir -p /stub/app && touch /stub/app/__init__.py && \
    cp pyproject.toml /stub/ && \
    pip install --no-cache-dir --prefix=/install /stub

# ── Layer 2: Application source ──────────────────────────────
# Copy the actual app code.  This layer is rebuilt whenever sources
# change, but the dependency layer above is reused.
COPY app/ /stub/app/

# Re-install to pick up the real app package (replaces the stub).
RUN pip install --no-cache-dir --prefix=/install /stub


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 2 — Runtime
# ═══════════════════════════════════════════════════════════════════════════════
FROM python:3.12-slim AS runtime

# ── Create non-root user ─────────────────────────────────────
RUN addgroup --system --gid 1001 qpilot && \
    adduser \
        --system \
        --uid 1001 \
        --no-create-home \
        --ingroup qpilot \
        --disabled-password \
        qpilot

WORKDIR /app

# ── Copy Python installation ─────────────────────────────────
COPY --from=builder /install /usr/local

# ── Copy application code ────────────────────────────────────
# The real app/ directory is available at /app/app/ via the working
# directory, which Python adds to sys.path automatically.
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .
COPY prompts/ prompts/

# ── Copy entrypoint script ───────────────────────────────────
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# ── Health check ─────────────────────────────────────────────
# Uses Python's built-in urllib so no curl/wget is needed in the image.
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; exit(0 if urllib.request.urlopen('http://localhost:8000/api/v1/health').status == 200 else 1)"

# ── Security & runtime setup ─────────────────────────────────
RUN chown -R qpilot:qpilot /app
USER qpilot

EXPOSE 8000

# exec-form CMD ensures SIGTERM reaches uvicorn for graceful shutdown
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
