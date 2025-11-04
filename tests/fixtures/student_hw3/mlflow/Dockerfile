# mlflow/Dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl jq && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

# Core libs for tracking + model serving + IO with MinIO/Redis
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Workdir with training script
WORKDIR /opt/mlflow
COPY train_model.py /opt/mlflow/train_model.py

# Expose ports: 5000 (tracking UI), 6000 (model serving)
EXPOSE 5000 6000
