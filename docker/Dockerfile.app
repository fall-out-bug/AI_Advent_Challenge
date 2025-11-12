FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt || true && \
    pip install --no-cache-dir transformers httpx prometheus-client

COPY src /app/src

CMD ["python", "-c", "print('summarizer app container')"]
