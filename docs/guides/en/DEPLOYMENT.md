# Butler Agent Deployment Guide

This guide provides step-by-step instructions for deploying Butler Agent in different environments: local development, Docker, and production.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Local Deployment](#local-deployment)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Python 3.10+**: Python runtime environment
- **MongoDB 7.0+**: Database for dialog context storage
- **Mistral API Service**: LLM service (local or remote)
  - Local: Mistral-7B via localhost:8001
  - Remote: Any Mistral-compatible API endpoint
- **Telegram Bot Token**: Bot token from [@BotFather](https://t.me/BotFather)

### Optional Software

- **Docker 20.10+**: For containerized deployment
- **Docker Compose 2.0+**: For multi-container orchestration
- **Poetry**: Python dependency management (recommended)

### System Requirements

**Minimum:**
- RAM: 2GB (for local development)
- Disk: 5GB free space
- Network: Internet connection for Telegram API

**Recommended (Production):**
- RAM: 4GB+ (for Mistral LLM if running locally)
- Disk: 10GB+ free space
- CPU: 4+ cores (for better performance)

## Environment Variables

Butler Agent requires the following environment variables:

### Required Variables

**`TELEGRAM_BOT_TOKEN`**
- Description: Telegram bot token from BotFather
- Example: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
- How to get: Message [@BotFather](https://t.me/BotFather) on Telegram and create a new bot

**`MONGODB_URL`**
- Description: MongoDB connection string
- Default: `mongodb://localhost:27017`
- Example: `mongodb://localhost:27017/butler_db`
- Format: `mongodb://[username:password@]host[:port]/[database]`

**`MISTRAL_API_URL`**
- Description: Mistral API base URL
- Default: `http://localhost:8001`
- Example: `http://localhost:8001` (local) or `https://api.mistral.ai` (remote)

### Optional Variables

**`LOG_LEVEL`**
- Description: Logging level
- Default: `INFO`
- Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**`MISTRAL_TIMEOUT`**
- Description: Mistral API timeout in seconds
- Default: `30`
- Example: `60`

**`MISTRAL_MAX_RETRIES`**
- Description: Maximum retry attempts for Mistral API
- Default: `3`
- Example: `5`

### Environment File Setup

Create a `.env` file in the project root:

```bash
# Required
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
MONGODB_URL=mongodb://localhost:27017/butler_db
MISTRAL_API_URL=http://localhost:8001

# Optional
LOG_LEVEL=INFO
MISTRAL_TIMEOUT=30
MISTRAL_MAX_RETRIES=3
```

**Security Note:** Never commit `.env` file to version control. Add it to `.gitignore`.

## Local Deployment

### Step 1: Install Dependencies

**Using Poetry (Recommended):**
```bash
# Install Poetry if not installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate virtual environment
poetry shell
```

**Using pip:**
```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Start MongoDB

**Using Docker (Recommended):**
```bash
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:7.0
```

**Using System Installation:**
```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod

# On macOS (Homebrew)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Verify MongoDB:**
```bash
# Check if MongoDB is running
mongosh --eval "db.adminCommand('ping')"
# Or
docker exec mongodb mongosh --eval "db.adminCommand('ping')"
```

### Step 3: Start Mistral API (If Local)

**Using Docker:**
```bash
docker run -d \
  --name mistral-api \
  -p 8001:8000 \
  --gpus all \
  vllm/vllm-openai:latest \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --tensor-parallel-size=1 \
  --dtype=float16
```

**Or use existing local model service:**
```bash
# Check if Mistral is already running on port 8001
curl http://localhost:8001/health
```

**For remote Mistral API:**
- Update `MISTRAL_API_URL` in `.env` to your remote endpoint
- Ensure authentication is configured if required

### Step 4: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your values
nano .env  # or use your preferred editor
```

**Required edits:**
1. Set `TELEGRAM_BOT_TOKEN` to your bot token
2. Verify `MONGODB_URL` matches your MongoDB setup
3. Verify `MISTRAL_API_URL` matches your Mistral setup

### Step 5: Run Butler Bot

**Using Poetry:**
```bash
poetry run python -m src.presentation.bot
```

**Using pip:**
```bash
python -m src.presentation.bot
```

**Or directly:**
```bash
python src/presentation/bot/__main__.py
```

**Expected Output:**
```
INFO:bot:Butler Bot starting...
INFO:factory:Creating ButlerOrchestrator...
INFO:factory:Initialized MongoDB connection
INFO:factory:Initialized MistralClient
INFO:factory:Initialized MCPToolClientAdapter
INFO:factory:ButlerOrchestrator created successfully
INFO:bot:Butler Bot started. Press Ctrl+C to stop.
```

### Step 6: Verify Bot is Running

1. Open Telegram and search for your bot (by name you set with BotFather)
2. Send `/start` command
3. You should receive a welcome message
4. Try a natural language message: "Buy milk tomorrow"

## Docker Deployment

### Docker Compose Setup

Create `docker-compose.butler.yml`:

```yaml
version: '3.9'

services:
  mongodb:
    image: mongo:7.0
    container_name: butler-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

  mistral-api:
    image: vllm/vllm-openai:latest
    container_name: butler-mistral
    ports:
      - "8001:8000"
    environment:
      - HF_TOKEN=${HF_TOKEN:-}
    command:
      - --model=mistralai/Mistral-7B-Instruct-v0.2
      - --tensor-parallel-size=1
      - --dtype=float16
      - --max-model-len=32768
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  butler-bot:
    build:
      context: .
      dockerfile: Dockerfile.bot
    container_name: butler-bot
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - MONGODB_URL=mongodb://mongodb:27017/butler_db
      - MISTRAL_API_URL=http://mistral-api:8000
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - MISTRAL_TIMEOUT=${MISTRAL_TIMEOUT:-30}
      - MISTRAL_MAX_RETRIES=${MISTRAL_MAX_RETRIES:-3}
    depends_on:
      mongodb:
        condition: service_healthy
      mistral-api:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; from src.presentation.bot.butler_bot import ButlerBot; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  mongodb_data:
```

### Build and Run

**Step 1: Build Images**
```bash
docker-compose -f docker-compose.butler.yml build
```

**Step 2: Set Environment Variables**
```bash
# Create .env file
cat > .env << EOF
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
MONGODB_URL=mongodb://mongodb:27017/butler_db
MISTRAL_API_URL=http://mistral-api:8000
LOG_LEVEL=INFO
MISTRAL_TIMEOUT=30
MISTRAL_MAX_RETRIES=3
EOF
```

**Step 3: Start Services**
```bash
docker-compose -f docker-compose.butler.yml up -d
```

**Step 4: View Logs**
```bash
# All services
docker-compose -f docker-compose.butler.yml logs -f

# Specific service
docker-compose -f docker-compose.butler.yml logs -f butler-bot
```

**Step 5: Stop Services**
```bash
docker-compose -f docker-compose.butler.yml down
```

### Docker Commands

```bash
# Start services
docker-compose -f docker-compose.butler.yml up -d

# Stop services
docker-compose -f docker-compose.butler.yml down

# Restart services
docker-compose -f docker-compose.butler.yml restart

# View logs
docker-compose -f docker-compose.butler.yml logs -f butler-bot

# Rebuild and restart
docker-compose -f docker-compose.butler.yml up -d --build

# Remove volumes (clean data)
docker-compose -f docker-compose.butler.yml down -v
```

## Production Deployment

### Production Considerations

**1. Security:**
- Use strong MongoDB credentials
- Store secrets in secure vault (AWS Secrets Manager, HashiCorp Vault, etc.)
- Enable TLS/SSL for MongoDB connections
- Restrict network access to MongoDB
- Use environment-specific `.env` files (not in version control)

**2. Scalability:**
- Use MongoDB replica set for high availability
- Consider multiple bot instances with load balancing
- Use message queue (RabbitMQ, Redis) for reliability
- Monitor resource usage (CPU, RAM, disk)

**3. Monitoring:**
- Set up Prometheus metrics collection
- Configure Grafana dashboards
- Set up alerting for errors and downtime
- Log aggregation (ELK stack, Loki)

**4. Backup:**
- Automated MongoDB backups
- Test restore procedures regularly
- Store backups off-site

### Production Environment Variables

```bash
# Production .env.example
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
MONGODB_URL=mongodb://username:password@mongodb-host:27017/butler_db?authSource=admin&tls=true
MISTRAL_API_URL=https://api.mistral.ai/v1
LOG_LEVEL=WARNING
MISTRAL_TIMEOUT=60
MISTRAL_MAX_RETRIES=5
```

### Production Docker Compose

**Enhanced production configuration:**

```yaml
version: '3.9'

services:
  mongodb:
    image: mongo:7.0
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGO_USERNAME}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASSWORD}
    volumes:
      - mongodb_data:/data/db
      - ./backups:/backups
    command: --replSet rs0 --bind_ip_all
    networks:
      - butler-network

  butler-bot:
    build:
      context: .
      dockerfile: Dockerfile.bot
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - MONGODB_URL=${MONGODB_URL}
      - MISTRAL_API_URL=${MISTRAL_API_URL}
    depends_on:
      - mongodb
    restart: always
    networks:
      - butler-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  butler-network:
    driver: bridge

volumes:
  mongodb_data:
```

### Systemd Service (Alternative)

For production deployments without Docker:

**Create `/etc/systemd/system/butler-bot.service`:**

```ini
[Unit]
Description=Butler Agent Telegram Bot
After=network.target mongod.service

[Service]
Type=simple
User=butler
WorkingDirectory=/opt/butler-bot
Environment="PATH=/opt/butler-bot/venv/bin"
EnvironmentFile=/opt/butler-bot/.env
ExecStart=/opt/butler-bot/venv/bin/python -m src.presentation.bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and Start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable butler-bot
sudo systemctl start butler-bot
sudo systemctl status butler-bot
```

## Verification

### Health Checks

**1. MongoDB Connectivity:**
```bash
# Local
mongosh --eval "db.adminCommand('ping')"

# Docker
docker exec butler-mongodb mongosh --eval "db.adminCommand('ping')"

# Python
python -c "from motor.motor_asyncio import AsyncIOMotorClient; import asyncio; asyncio.run(AsyncIOMotorClient('mongodb://localhost:27017').admin.command('ping'))"
```

**2. Mistral API Availability:**
```bash
# Health check
curl http://localhost:8001/health

# Or test endpoint
curl http://localhost:8001/v1/models
```

**3. Butler Bot Module:**
```bash
# Import test
python -c "from src.presentation.bot.butler_bot import ButlerBot; print('OK')"

# Factory test
python -c "from src.presentation.bot.factory import create_butler_orchestrator; import asyncio; asyncio.run(create_butler_orchestrator()); print('OK')"
```

### Telegram Bot Verification

**1. Send Test Message:**
- Open Telegram
- Find your bot
- Send `/start`
- Expected: Welcome message

**2. Test Natural Language:**
- Send: "Buy milk tomorrow"
- Expected: Task creation response or clarification request

**3. Test Different Modes:**
- TASK: "Create a task to call John"
- DATA: "Show me channel digests"
- REMINDERS: "List my reminders"
- IDLE: "Hello, how are you?"

### Log Verification

**Check for Errors:**
```bash
# Docker logs
docker-compose -f docker-compose.butler.yml logs butler-bot | grep -i error

# Local logs (if logging to file)
tail -f /var/log/butler-bot.log | grep -i error
```

**Expected Log Patterns:**
- `INFO:factory:ButlerOrchestrator created successfully`
- `INFO:bot:Butler Bot started`
- No `ERROR` or `CRITICAL` messages

## Troubleshooting

### Common Issues

#### 1. Bot Not Responding

**Symptoms:** Bot doesn't respond to messages

**Diagnosis:**
```bash
# Check if bot is running
docker ps | grep butler-bot
# Or
ps aux | grep butler

# Check logs
docker-compose logs butler-bot
```

**Solutions:**
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Check internet connectivity
- Verify bot is not blocked
- Restart bot: `docker-compose restart butler-bot`

#### 2. MongoDB Connection Error

**Symptoms:** `pymongo.errors.ServerSelectionTimeoutError`

**Diagnosis:**
```bash
# Check MongoDB status
docker ps | grep mongodb
# Or
sudo systemctl status mongod

# Test connection
mongosh --eval "db.adminCommand('ping')"
```

**Solutions:**
- Verify MongoDB is running
- Check `MONGODB_URL` is correct
- Check firewall rules (port 27017)
- Verify network connectivity between services

#### 3. Mistral API Unavailable

**Symptoms:** `MistralConnectionError` or `MistralTimeoutError`

**Diagnosis:**
```bash
# Check Mistral API
curl http://localhost:8001/health

# Check logs
docker-compose logs mistral-api
```

**Solutions:**
- Verify Mistral API is running
- Check `MISTRAL_API_URL` is correct
- Increase timeout: `MISTRAL_TIMEOUT=60`
- Check GPU availability (if using local Mistral)
- Fallback: System will use IDLE mode if LLM unavailable

#### 4. Import Errors

**Symptoms:** `ModuleNotFoundError` or `ImportError`

**Diagnosis:**
```bash
# Check Python environment
which python
python --version

# Check dependencies
pip list | grep -E "aiogram|motor|pydantic"
```

**Solutions:**
- Reinstall dependencies: `poetry install` or `pip install -r requirements.txt`
- Verify virtual environment is activated
- Check `PYTHONPATH` environment variable

#### 5. Handler Errors

**Symptoms:** "Something went wrong" messages to users

**Diagnosis:**
```bash
# Check handler logs
docker-compose logs butler-bot | grep -i "handler\|error"

# Check specific handler
docker-compose logs butler-bot | grep -i "TaskHandler\|DataHandler"
```

**Solutions:**
- Check MCP tools are available
- Verify tool schemas are correct
- Check user permissions for MCP tools
- Review handler implementation logs

#### 6. State Machine Issues

**Symptoms:** Context not persisting between messages

**Diagnosis:**
```bash
# Check MongoDB collections
mongosh butler_db --eval "db.dialog_contexts.find().pretty()"

# Check context save logs
docker-compose logs butler-bot | grep -i "context\|state"
```

**Solutions:**
- Verify MongoDB connection
- Check collection permissions
- Review context save/load logic
- Check for database errors in logs

### Log Analysis

**View Real-time Logs:**
```bash
# Docker
docker-compose -f docker-compose.butler.yml logs -f butler-bot

# Systemd
sudo journalctl -u butler-bot -f
```

**Filter Logs:**
```bash
# Errors only
docker-compose logs butler-bot | grep -i error

# Specific component
docker-compose logs butler-bot | grep -i orchestrator

# Time range
docker-compose logs butler-bot --since 1h
```

### Performance Issues

**Symptoms:** Slow responses, high CPU/RAM usage

**Diagnosis:**
```bash
# Check resource usage
docker stats butler-bot

# Check MongoDB performance
mongosh --eval "db.currentOp()"
```

**Solutions:**
- Increase Mistral API timeout if slow
- Add MongoDB indexes for faster queries
- Consider caching for frequent requests
- Scale horizontally if needed

### Getting Help

If issues persist:

1. **Check Documentation:**
   - [Architecture Documentation](ARCHITECTURE.md)
   - [API Documentation](API.md)
   - [Testing Documentation](TESTING.md)

2. **Review Logs:**
   - Enable `DEBUG` logging: `LOG_LEVEL=DEBUG`
   - Review error messages carefully
   - Check stack traces

3. **Verify Environment:**
   - All prerequisites installed
   - Environment variables set correctly
   - Services running and accessible

4. **Test Components:**
   - Run unit tests: `make test-unit`
   - Run integration tests: `make test-integration`
   - Run E2E tests: `make test-e2e`

## Next Steps

After successful deployment:

1. **Set Up Monitoring:**
   - Configure Prometheus metrics
   - Set up Grafana dashboards
   - Configure alerting

2. **Backup Strategy:**
   - Schedule MongoDB backups
   - Test restore procedures

3. **Performance Tuning:**
   - Monitor response times
   - Optimize database queries
   - Cache frequently accessed data

4. **Documentation:**
   - Document custom configurations
   - Update team on deployment procedures

## References

- [Architecture Documentation](ARCHITECTURE.md) - System architecture
- [API Documentation](API.md) - API reference
- [Testing Documentation](TESTING.md) - Testing guidelines
- [Telegram Bot API](https://core.telegram.org/bots/api) - Telegram API documentation
- [MongoDB Documentation](https://docs.mongodb.com/) - MongoDB guides
