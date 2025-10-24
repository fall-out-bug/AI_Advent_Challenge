FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install system dependencies and Python packages in a single layer
RUN apt-get update && \
    apt-get install -y python3 python3-pip git curl build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install --upgrade pip && \
    pip3 install torch==2.1.0 torchvision --extra-index-url https://download.pytorch.org/whl/cu121 && \
    pip3 install transformers accelerate bitsandbytes fastapi uvicorn auto-gptq optimum && \
    pip3 install flash-attn --no-build-isolation || echo "Flash-attn installation failed, continuing without it"

# Copy application code and set ownership
COPY --chown=appuser:appuser chat_api.py .

# Create cache directory with proper ownership and permissions
RUN mkdir -p /home/appuser/.cache/huggingface && \
    chown -R appuser:appuser /home/appuser/.cache && \
    chmod -R 755 /home/appuser/.cache

# Switch to non-root user
USER appuser

# Build arguments and environment variables
ARG MODEL_NAME=Qwen/Qwen1.5-4B-Chat
ENV MODEL_NAME=${MODEL_NAME}
ENV HF_HOME=/home/appuser/.cache/huggingface

# Expose port
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "chat_api:app", "--host", "0.0.0.0", "--port", "8000"]
