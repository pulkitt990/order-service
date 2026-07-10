# ─────────────────────────────────────────────────────────────
# Stage 1: Builder
# Installs dependencies into a clean virtual environment
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS builder

# Don't write .pyc files, don't buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Patch OS-level packages to reduce CVE surface
RUN apt-get update && apt-get upgrade -y --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Install deps first (layer-cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─────────────────────────────────────────────────────────────
# Stage 2: Runtime
# Minimal final image — no build tools, no pip, no cache
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS runtime

# Security: run as non-root user
# Patch OS packages in runtime stage too
RUN apt-get update && apt-get upgrade -y --no-install-recommends && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid appuser --shell /bin/bash --create-home appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

WORKDIR /app

# Copy only the installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY src/ ./src/

# Switch to non-root user
USER appuser

# Expose app port
EXPOSE 8000

# Health check — Kubernetes also uses /health but this adds Docker-native checking
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Start with uvicorn — production settings
# --workers 1: single worker so metrics are not split across processes
# --host 0.0.0.0: listen on all interfaces inside container
CMD ["uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info", \
     "--access-log"]
