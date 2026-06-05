# Build from the REPO ROOT so the shared lib is available:
#   docker compose build   (compose sets context: . for us)
FROM python:3.11-slim

WORKDIR /app

COPY libs/common /app/libs/common
COPY services/aggregation-service /app/services/aggregation-service

RUN pip install --no-cache-dir -e /app/libs/common -e /app/services/aggregation-service

VOLUME ["/app/data"]
ENTRYPOINT ["aggregation-service"]
