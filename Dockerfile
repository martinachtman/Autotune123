# Autotune123 Dockerfile - Modern Python implementation without bash/JavaScript dependencies
FROM python:3.9-slim

# Install only essential system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    jq \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash autotune

# Set working directory
WORKDIR /app/Autotune123

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application files (excluding sensitive files via .dockerignore)
COPY *.py ./
COPY api/ ./api/
COPY assets/ ./assets/
COPY data_processing/ ./data_processing/
COPY layout/ ./layout/

# Create directories for autotune operations (legacy compatibility)
RUN mkdir -p /app/Autotune123/myopenaps/settings /root/myopenaps/settings \
    && chown -R autotune:autotune /app/Autotune123

# Set environment variables
ENV PYTHONPATH="/app/Autotune123:${PYTHONPATH}"
ENV ENV=production
ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER autotune

# Expose the port the app runs on
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Command to run the application
CMD ["python", "wsgi.py"]