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
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8005"]

