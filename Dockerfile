# AGNTCon + MCPCon Europe 2026 - Production Hub Dockerfile
# Lightweight, secure, zero-root container image

FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8088 \
    HOST=0.0.0.0

WORKDIR /app

# Install curl for container healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install minimal Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root system user
RUN groupadd -g 10001 hubgroup && \
    useradd -u 10001 -g hubgroup -s /bin/sh -d /app hubuser

# Copy application files and website assets
COPY serve.py mcp_server.py crm_db.py .
COPY site/ site/
COPY data/ data/

# Ensure appropriate permissions for persistent SQLite databases
RUN mkdir -p /app/data && chown -R hubuser:hubgroup /app

USER hubuser

EXPOSE 8088

# Healthcheck monitoring the zero-allocation queue telemetry endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8088/api/queue-status || exit 1

ENTRYPOINT ["python", "serve.py", "--host", "0.0.0.0", "--port", "8088"]
