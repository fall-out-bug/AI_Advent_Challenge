# Development Environment Setup

## Local Environment (Docker Compose)

### docker-compose.yml
```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:7.0
    ports: ["27017:27017"]
    environment:
      MONGO_INITDB_DATABASE: payments_dev
    volumes:
      - mongo_data:/data/db

  redis:
    image: redis:7.2-alpine
    ports: ["6379:6379"]

  prometheus:
    image: prom/prometheus:v2.47.0
    ports: ["9090:9090"]
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml

  app:
    build: .
    ports: ["8000:8000"]
    environment:
      MONGODB_URI: mongodb://mongodb:27017/payments_dev
      REDIS_URL: redis://redis:6379
      LOG_LEVEL: DEBUG
    depends_on: [mongodb, redis]
    volumes:
      - ./src:/app/src  # Hot reload
      - ./tests:/app/tests

volumes:
  mongo_data:
```

### Setup Commands
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app

# Run tests in container
docker-compose exec app pytest tests/

# Stop all
docker-compose down
```

## Python Environment (Poetry)

### pyproject.toml
```toml
[tool.poetry]
name = "payment-service"
version = "1.0.0"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
pymongo = "^4.6.0"
redis = "^5.0.0"
pydantic = "^2.5.0"
prometheus-client = "^0.19.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
black = "^23.11.0"
flake8 = "^6.1.0"
mypy = "^1.7.0"
```

### Setup
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run tests
poetry run pytest

# Type check
poetry run mypy src/

# Format code
poetry run black src/ tests/
```

## VS Code Configuration

### .vscode/settings.json
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.rulers": [88]
}
```

**Result:** Consistent environment across team, "works on my machine" eliminated
