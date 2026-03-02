# ============================================================
# Dockerfile for IBM Code Engine Deployment
# Telegram Calorie Tracker Bot
# ============================================================

# Use official Python slim image for smaller footprint
FROM --platform=linux/amd64 python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8080

# Set working directory
WORKDIR /app

# Install system dependencies required for:
# - psycopg2 (PostgreSQL adapter): libpq-dev, gcc
# - matplotlib (graph generation): libfreetype6-dev, libpng-dev, pkg-config
# - General build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libfreetype6-dev \
    libpng-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching optimization)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create a non-root user for security (IBM Code Engine best practice)
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

# Create graphs directory with correct permissions
RUN mkdir -p /app/graphs && chown -R appuser:appuser /app/graphs

USER appuser

# IBM Code Engine uses port 8080 by default
EXPOSE 8080

# Health check — Code Engine uses HTTP probes
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Start the unified application (API + webhook bot)
# Uses gunicorn for production-grade WSGI serving
CMD ["gunicorn", "src.api.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:8080", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]