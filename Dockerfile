# ============================================================
# SEO Health Report System - Production Dockerfile
# Multi-stage build for API and Worker services
# ============================================================

# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for caching
COPY pyproject.toml ./
COPY packages/ ./packages/

# Install Python dependencies and create wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir=/wheels .

# ============================================================
# Stage 2: Production base image
# ============================================================
FROM python:3.11-slim AS production

# Labels
LABEL maintainer="RaapTech LLC"
LABEL description="SEO Health Report System"
LABEL version="1.0.0"

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# Install uvicorn for API server
RUN pip install --no-cache-dir uvicorn[standard]

# Copy application code
COPY --chown=appuser:appgroup . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/reports /app/logs /app/storage /app/data && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Default environment variables
ENV DATABASE_URL=sqlite:///./data/seo_health.db \
    REPORT_TIER=medium \
    LOG_LEVEL=INFO \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    PYTHONPATH=/app

# Expose port
EXPOSE 8000

# ============================================================
# Stage 3: API Service
# ============================================================
FROM production AS api

# Health check for API
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${API_PORT}/health || exit 1

# API server command
CMD ["python", "-m", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================================
# Stage 4: Worker Service
# ============================================================
FROM production AS worker

# Worker-specific environment
ENV WORKER_POLL_INTERVAL=5 \
    WORKER_LEASE_SECONDS=300

# Health check for worker (check if process is running)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "apps.worker.main" || exit 1

# Worker command
CMD ["python", "-m", "apps.worker.main"]
