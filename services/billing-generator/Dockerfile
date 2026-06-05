# Build from the REPO ROOT so the shared lib is available:
#   docker compose build   (compose sets context: . for us)
FROM python:3.11-slim

WORKDIR /app

# Shared contract first (better layer caching), then the service.
COPY libs/common /app/libs/common
COPY services/billing-generator /app/services/billing-generator

RUN pip install --no-cache-dir -e /app/libs/common -e /app/services/billing-generator

# Default: stream synthetic billing to stdout (override via env / compose)
ENV BILLING_SINK=stdout
ENTRYPOINT ["billing-generator"]
