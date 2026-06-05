# Build from the REPO ROOT so the shared lib is available:
#   docker compose build   (compose sets context: . for us)
FROM python:3.11-slim

WORKDIR /app

# Shared contract first (better layer caching), then the service.
COPY libs/common /app/libs/common
COPY services/ingestion-service /app/services/ingestion-service

RUN pip install --no-cache-dir -e /app/libs/common -e /app/services/ingestion-service

# Landed data (SQLite + dead-letter) goes here; mount a volume to persist it.
VOLUME ["/app/data"]
ENTRYPOINT ["ingestion-service"]
