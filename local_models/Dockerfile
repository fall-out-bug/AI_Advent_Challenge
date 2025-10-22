FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

RUN apt-get update && \
    apt-get install -y python3 python3-pip git && \
    apt-get clean

RUN pip3 install --upgrade pip
RUN pip3 install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu117
RUN pip3 install transformers accelerate bitsandbytes fastapi uvicorn

WORKDIR /app
COPY chat_api.py .

ARG MODEL_NAME=Qwen/Qwen1.5-4B-Chat
ENV MODEL_NAME=${MODEL_NAME}

CMD ["uvicorn", "chat_api:app", "--host", "0.0.0.0", "--port", "8000"]
