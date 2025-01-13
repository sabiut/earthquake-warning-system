FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive
ENV DJANGO_SETTINGS_MODULE earthquake_warning.settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    netcat-openbsd \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install additional Gunicorn dependencies
RUN pip install --no-cache-dir \
    gevent \
    setproctitle

# Create directories for static and media files
RUN mkdir -p /app/earthquake_warning/static
RUN mkdir -p /app/earthquake_warning/staticfiles
RUN mkdir -p /app/earthquake_warning/media

# Set permissions
RUN chmod -R 755 /app/earthquake_warning/static
RUN chmod -R 755 /app/earthquake_warning/staticfiles
RUN chmod -R 755 /app/earthquake_warning/media

# Copy project files
COPY ./earthquake_warning /app/earthquake_warning/
COPY entrypoint.sh /app/

# Set permissions for entrypoint
RUN chmod +x /app/entrypoint.sh

# Make sure the Python path includes our application
ENV PYTHONPATH=/app

ENTRYPOINT ["/app/entrypoint.sh"]