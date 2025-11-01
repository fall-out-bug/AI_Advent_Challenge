FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install system dependencies with apt cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y python3 python3-pip git curl build-essential gosu && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install base Python packages (lightweight dependencies first)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install --upgrade pip && \
    pip3 install prometheus-client fastapi uvicorn

# Install PyTorch and vision (heavy but stable)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install torch==2.1.0 torchvision --extra-index-url https://download.pytorch.org/whl/cu121

# Install ML libraries and protobuf (needed for newer Mistral models)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install "protobuf>=3.20.3,<5" sentencepiece safetensors transformers accelerate bitsandbytes auto-gptq optimum

# Install flash-attn separately (heaviest, longest build time - cached separately)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install flash-attn --no-build-isolation || echo "Flash-attn installation failed, continuing without it"

# Copy application code and entrypoint script
COPY --chown=appuser:appuser chat_api.py .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create cache directory with proper ownership and permissions
RUN mkdir -p /home/appuser/.cache/huggingface/hub && \
    chown -R appuser:appuser /home/appuser/.cache && \
    chmod -R 777 /home/appuser/.cache

# Entrypoint script (runs as root to fix permissions, then switches to appuser)
ENTRYPOINT ["/entrypoint.sh"]

# Don't switch user here - entrypoint will do it
# USER appuser

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
