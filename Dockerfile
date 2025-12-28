# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
# - gcc: Required for compiling some Python packages
# - default-libmysqlclient-dev: Required for mysqlclient
# - pkg-config: Required for building MySQL client library
# - curl: For health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt /app/
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy project files
COPY . /app/

# Create directories for static files and media
# These directories will be used by collectstatic and for storing user uploads
# Note: These directories will be overridden by Docker volumes in docker-compose.yml
#       The volume mounts ensure data persistence and sharing between containers
#       - static_volume:/app/staticfiles (shared between web and nginx containers)
#       - media_volume:/app/media (shared between web, nginx, and celery containers)
# Note: collectstatic is run at container startup (in docker-compose.yml command),
#       not during build, to ensure database is available and all migrations are applied
RUN mkdir -p /app/staticfiles /app/media

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Add metadata labels for image management
LABEL maintainer="Task Management System" \
      version="1.0" \
      description="Task Management System - Django REST API with Celery" \
      org.opencontainers.image.title="Task Management System" \
      org.opencontainers.image.description="Production-ready Django REST API for task management with Celery background tasks" \
      org.opencontainers.image.vendor="Task Management System" \
      org.opencontainers.image.version="1.0" \
      org.opencontainers.image.authors="Task Management System Team"

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check configuration
# Checks the /health/ endpoint every 30 seconds
# Allows 10 seconds for the check to complete
# Waits 40 seconds before starting health checks (startup time)
# Retries 3 times before marking as unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command (can be overridden in docker-compose.yml)
# Uses gunicorn_config.py for comprehensive configuration
CMD ["gunicorn", "taskmanager.wsgi:application", "--config", "gunicorn_config.py"]

