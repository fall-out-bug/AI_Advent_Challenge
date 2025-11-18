<<<<<<< HEAD
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY docker/whisper-server/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy server code
COPY docker/whisper-server/server.py /app/server.py
WORKDIR /app

# Expose port
EXPOSE 8005

# Run server
=======
# Use CUDA base image for GPU support
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Install Python dependencies with CUDA support
# Install PyTorch with CUDA first
RUN pip install --no-cache-dir \
    torch==2.1.0+cu121 \
    torchaudio==2.1.0+cu121 \
    --index-url https://download.pytorch.org/whl/cu121

# Install other dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    python-multipart==0.0.6 \
    "numpy<2.0" \
    openai-whisper==20231117

# Copy server code
COPY docker/whisper-server/server.py /app/server.py

EXPOSE 8005

>>>>>>> origin/master
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8005"]
