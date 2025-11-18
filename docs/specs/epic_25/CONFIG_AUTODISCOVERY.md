# Service Auto-Discovery Configuration

**Epic**: EP25
**Status**: ✅ Implemented

---

## Overview

All services now use **Docker service discovery** with sensible defaults. No manual configuration needed!

---

## How It Works

### 1. Docker Service Names as Defaults

All defaults use Docker service names that work automatically in `docker-compose` networks:

| Service | Default | Docker Service Name |
|---------|---------|---------------------|
| MongoDB | `mongodb://shared-mongo:27017/butler?authSource=admin` | `shared-mongo` |
| LLM API | `http://llm-api:8000` | `llm-api` |
| Whisper STT | `whisper-stt:8005` | `whisper-stt` |
| Redis | `shared-redis:6379` | `shared-redis` |
| MCP Server | `http://mcp-server:8004` | `mcp-server` |

### 2. Settings.py Defaults

Updated `src/infrastructure/config/settings.py`:

```python
mongodb_url: str = Field(
    default="mongodb://shared-mongo:27017/butler?authSource=admin",
    description="MongoDB (uses Docker service 'shared-mongo')"
)

llm_url: str = Field(
    default="http://llm-api:8000",
    description="LLM service (uses Docker service 'llm-api')"
)
```

### 3. Docker Compose Environment

`docker-compose.butler.yml` uses service names as defaults:

```yaml
environment:
  - MONGODB_URL=${MONGODB_URL:-mongodb://shared-mongo:27017/...}
  - LLM_URL=${LLM_URL:-http://llm-api:8000}
  - WHISPER_HOST=${WHISPER_HOST:-whisper-stt}
  - VOICE_REDIS_HOST=${VOICE_REDIS_HOST:-shared-redis}
```

---

## Usage

### Standard Deployment (Zero Config)

```bash
# Just start services - everything auto-discovered!
./scripts/infra/start_shared_infra.sh
make butler-up
```

**No configuration needed!** All services use Docker service names.

### Custom Configuration (Optional)

If you need custom URLs:

```bash
# Option 1: .env file
echo "LLM_URL=http://custom-llm:8000" >> .env

# Option 2: Environment variable
export LLM_URL="http://custom-llm:8000"
make butler-up
```

---

## Benefits

✅ **Zero Configuration**: Works out of the box
✅ **Docker Native**: Uses Docker service discovery
✅ **Network Aware**: Automatically works in Docker networks
✅ **Override Friendly**: Can still customize if needed
✅ **Consistent**: Same service names everywhere

---

## Migration Notes

### Before
- Had to manually set `MONGODB_URL`, `LLM_URL`, etc.
- Different URLs for local vs Docker
- Easy to misconfigure

### After
- Defaults work automatically
- Docker service names used everywhere
- Can override if needed

---

**Result**: Never need to configure MongoDB, LLM, or other services manually again! 🎉
