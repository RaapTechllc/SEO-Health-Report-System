# Multi-stage build for SEO Health Report Worker
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies first (for layer caching)
COPY pyproject.toml .
COPY packages/ packages/
RUN pip install --no-cache-dir --prefix=/install -e .

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

# Build arguments for versioning
ARG VERSION=0.0.0
ARG GIT_SHA=unknown
ARG BUILD_DATE=unknown

# Labels for metadata
LABEL org.opencontainers.image.title="SEO Health Report Worker"
LABEL org.opencontainers.image.description="Background worker for SEO Health Report System"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.revision="${GIT_SHA}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.source="https://github.com/RaapTechllc/SEO-Health-Report-System"
LABEL org.opencontainers.image.vendor="RaapTech LLC"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /app/reports /app/logs /app/storage /tmp \
    && chown -R appuser:appuser /app/reports /app/logs /app/storage

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_VERSION=${VERSION} \
    GIT_SHA=${GIT_SHA} \
    WORKER_HEARTBEAT_FILE=/tmp/worker_heartbeat

# Switch to non-root user
USER appuser

# Health check - worker writes heartbeat file
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD test -f /tmp/worker_heartbeat && \
        test $(($(date +%s) - $(stat -c %Y /tmp/worker_heartbeat 2>/dev/null || echo 0))) -lt 60 || exit 1

# Run worker
CMD ["python", "apps/worker/main.py"]
