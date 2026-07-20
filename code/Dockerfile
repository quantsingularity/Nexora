# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /app

# System deps needed to compile wheels (numpy, torch, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only torch to keep image size reasonable in containers
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
        torch==2.1.0+cpu \
        --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.10-slim AS runtime

WORKDIR /app

# Runtime system libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY . .

# Create runtime directories
RUN mkdir -p audit data/synthetic data/processed models logs

# Non-root user for security
RUN useradd -m -u 1000 nexora && chown -R nexora:nexora /app
USER nexora

# Expose REST API port
EXPOSE 8000

# Expose gRPC port
EXPOSE 50051

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    AUDIT_DB_PATH=/app/audit/phi_access.db \
    FHIR_SERVER_URL=http://mock-fhir-server/R4 \
    GRPC_PORT=50051

CMD uvicorn backend.serving.rest_api:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000}
