# Automatic Service Configuration Guide

**Epic**: EP25 - Personalised Butler
**Purpose**: Zero-configuration setup using Docker service discovery

---

## Problem

Previously, services required manual configuration of URLs:
- MongoDB: `mongodb://localhost:27017` (doesn't work in Docker)
- LLM: `http://mistral-chat:8000` (wrong service name)
- Redis: Various hostnames

## Solution

Use **Docker service discovery** with sensible defaults that work "out of the box":

1. **Docker service names** as defaults (work in Docker networks)
2. **Environment variable overrides** for custom setups
3. **Automatic fallbacks** for local development

---

## Configuration Strategy

### 1. Settings.py Defaults

All defaults use **Docker service names** that work in `docker-compose`:

```python
mongodb_url: str = Field(
    default="mongodb://shared-mongo:27017/butler?authSource=admin",
    description="MongoDB (uses Docker service 'shared-mongo')"
)

llm_url: str = Field(
    default="http://llm-api:8000",
    description="LLM service (uses Docker service 'llm-api')"
)

whisper_host: str = Field(
    default="whisper-stt",
    description="Whisper STT (uses Docker service 'whisper-stt')"
)

voice_redis_host: str = Field(
    default="shared-redis",
    description="Redis (uses Docker service 'shared-redis')"
)
```

### 2. Docker Compose Environment

Use **simple defaults** that match Docker service names:

```yaml
environment:
  # MongoDB: Use service name, credentials from shared infra
  - MONGODB_URL=${MONGODB_URL:-mongodb://shared-mongo:27017/butler?authSource=admin}

  # LLM: Use service name
  - LLM_URL=${LLM_URL:-http://llm-api:8000}

  # Whisper: Use service name
  - WHISPER_HOST=${WHISPER_HOST:-whisper-stt}
  - WHISPER_PORT=${WHISPER_PORT:-8005}

  # Redis: Use service name
  - VOICE_REDIS_HOST=${VOICE_REDIS_HOST:-shared-redis}
```

### 3. Service Discovery Rules

**Docker Compose Network**:
- Services in same `docker-compose.yml` → use service name
- Services in shared infra → use service name from shared network
- Services connected via `networks:` → use service name

**Examples**:
- `shared-mongo` → accessible as `shared-mongo:27017`
- `llm-api` → accessible as `llm-api:8000`
- `whisper-stt` → accessible as `whisper-stt:8005`
- `shared-redis` → accessible as `shared-redis:6379`

---

## Benefits

✅ **Zero Configuration**: Works out of the box with `make butler-up`
✅ **Docker Native**: Uses Docker service discovery
✅ **Override Friendly**: Can still override via `.env` or environment
✅ **Network Aware**: Automatically works in Docker networks
✅ **Local Dev**: Can override for local development if needed

---

## Migration

### Before (Manual Config Required)
```bash
# Had to set manually
export MONGODB_URL="mongodb://admin:pass@localhost:27017/butler"
export LLM_URL="http://localhost:8000"
# etc...
```

### After (Automatic)
```bash
# Just works!
make butler-up
# All services auto-discovered via Docker service names
```

---

## Override for Custom Setups

If you need custom configuration:

```bash
# Option 1: .env file
echo "LLM_URL=http://custom-llm:8000" >> .env

# Option 2: Environment variable
export LLM_URL="http://custom-llm:8000"
make butler-up

# Option 3: docker-compose override
docker-compose -f docker-compose.butler.yml up -d \
  -e LLM_URL=http://custom-llm:8000
```

---

## Service Name Reference

| Service | Docker Name | Default URL/Config |
|---------|-------------|-------------------|
| MongoDB | `shared-mongo` | `mongodb://shared-mongo:27017/butler?authSource=admin` |
| LLM API | `llm-api` | `http://llm-api:8000` |
| Whisper STT | `whisper-stt` | `whisper-stt:8005` |
| Redis | `shared-redis` | `shared-redis:6379` |
| MCP Server | `mcp-server` | `http://mcp-server:8004` |

---

**Status**: ✅ Implemented
**Result**: Zero-configuration deployment using Docker service discovery
