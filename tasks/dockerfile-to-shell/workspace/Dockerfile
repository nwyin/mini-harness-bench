# Stage 1: Builder (dependencies)
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final application
FROM python:3.12-slim

# Environment configuration
ENV APP_NAME=warehouse-api
ENV APP_VERSION=2.1.0
ENV APP_ENV=production
ENV LOG_LEVEL=warning
ENV DB_HOST=localhost
ENV DB_PORT=5432
ENV CACHE_TTL=3600
ENV MAX_WORKERS=4
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create app directory structure
WORKDIR /app

RUN mkdir -p /app/src /app/config /app/data /app/logs

# Copy dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy application code
COPY src/ /app/src/
COPY config/settings.json /app/config/settings.json
COPY config/logging.yaml /app/config/logging.yaml

# Create a health check file
RUN echo '{"status": "ok", "version": "2.1.0"}' > /app/health.json

# Copy requirements for reference
COPY requirements.txt /app/requirements.txt

EXPOSE 8080

CMD ["python", "-m", "src.main"]
