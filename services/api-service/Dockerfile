# Build from the REPO ROOT so the shared lib is available:
#   docker compose build   (compose sets context: . for us)
FROM python:3.11-slim

WORKDIR /app

COPY libs/common /app/libs/common
COPY services/api-service /app/services/api-service

RUN pip install --no-cache-dir -e /app/libs/common -e /app/services/api-service

EXPOSE 8000
ENV API_HOST=0.0.0.0 API_PORT=8000
VOLUME ["/app/data"]
ENTRYPOINT ["api-service"]
