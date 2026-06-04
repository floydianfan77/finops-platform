FROM python:3.11-slim

WORKDIR /app

# Install the package first (better layer caching)
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e .

# Default: stream synthetic billing to stdout (override via env / compose)
ENV BILLING_SINK=stdout
ENTRYPOINT ["billing-generator"]
