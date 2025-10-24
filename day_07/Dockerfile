# Multi-stage build for better security and smaller image size
FROM python:3.10-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy shared SDK first (as it's a dependency)
COPY --chown=1000:1000 shared /shared

# Copy Poetry configuration files
COPY --chown=1000:1000 pyproject.toml poetry.lock ./
COPY --chown=1000:1000 pyproject.docker.toml ./

# Use Docker-specific pyproject.toml
RUN cp pyproject.docker.toml pyproject.toml

# Install Python dependencies with Poetry
RUN poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --only=main --no-root

# Production stage
FROM python:3.10-slim AS production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy shared SDK
COPY --chown=appuser:appuser shared /shared

# Copy application code and set ownership
COPY --chown=appuser:appuser . .

# Create results directory with proper ownership
RUN mkdir -p results && chown -R appuser:appuser results

# Switch to non-root user
USER appuser

# Expose ports (will be overridden by docker-compose)
EXPOSE 9001 9002

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9001/health || exit 1

# Default command (will be overridden by docker-compose)
CMD ["python", "-m", "uvicorn", "agents.api.generator_api:app", "--host", "0.0.0.0", "--port", "9001"]
