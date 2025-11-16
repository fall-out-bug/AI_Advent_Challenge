# Cluster A · MongoClient Usage Inventory

**Epic:** EP24 – Repository Hygiene & De-Legacy  
**Cluster:** A – Mongo & Async Infrastructure  
**Date:** 2025-11-16  
**Task:** A.1 – Inventory MongoClient usages

## Direct `MongoClient(...)` Instantiations

### 1. `src/presentation/cli/rag_commands.py` (Line 48)
```python
mongo_client = MongoClient(settings.mongodb_url)
database = mongo_client[settings.embedding_mongo_database]
```
**Context:** RAG comparison CLI command  
**Usage:** Sync MongoClient for embedding index access  
**Migration:** Replace with DI-based client factory

### 2. `src/presentation/cli/embedding_index.py` (Line 127)
```python
def _create_mongo_client(url: str, timeout_ms: int) -> MongoClient:
    """Create MongoDB client."""
    sanitized_url = _resolve_mongo_url(url)
    return MongoClient(sanitized_url, serverSelectionTimeoutMS=timeout_ms)
```
**Context:** Helper function for embedding index CLI  
**Usage:** Factory function creating sync MongoClient  
**Migration:** Refactor to use DI-based factory with Settings

## Existing Async Infrastructure

### `src/infrastructure/database/mongo.py`
- **`get_client()`** — Returns singleton `AsyncIOMotorClient` using `settings.mongodb_url`
- **`get_db()`** — Returns singleton `AsyncIOMotorDatabase` using `settings.db_name`
- **`close_client()`** — Cleanup function

**Status:** ✅ Already uses DI via `get_settings()`  
**Note:** This is async infrastructure. Sync clients in CLI still need refactoring.

## Settings Status

### `src/infrastructure/config/settings.py`
- **`mongodb_url`** — ✅ Exists (production MongoDB URL)
- **`test_mongodb_url`** — ✅ Added (defaults to `mongodb://localhost:27017`, can override via `TEST_MONGODB_URL` env var)

## Summary

**Direct Instantiations Found:** 2  
- Both in CLI modules (`rag_commands.py`, `embedding_index.py`)
- Both use sync `MongoClient` (not async)

**Migration Status:**
- ✅ `test_mongodb_url` added to Settings
- ✅ `MongoClientFactory` created for DI-based client creation
- ✅ Direct instantiations replaced with factory:
  - `rag_commands.py` — ✅ Migrated to use `MongoClientFactory`
  - `embedding_index.py` — ✅ Migrated (with fallback for compatibility)
- ✅ Shared fixtures created in `tests/conftest.py`:
  - `mongodb_client` (session-scoped)
  - `mongodb_database` (function-scoped, per-test DB with cleanup)

**Existing Infrastructure:**
- Async infrastructure (`mongo.py`) already uses DI ✅
- Sync infrastructure refactored to use DI ✅

**Next Steps:**
1. ✅ Inventory complete
2. ✅ Factory created
3. ✅ Direct instantiations migrated
4. ✅ Fixtures created
5. ⏳ Migrate repository tests to use shared fixtures
6. ⏳ Migrate worker tests to use shared fixtures
7. ⏳ Migrate channel tests to use shared fixtures
8. ⏳ Migrate evaluation tests to use shared fixtures

---

_Inventory completed by cursor_dev_a_v1 · 2025-11-16_  
_Migration completed by cursor_dev_a_v1 · 2025-11-16_

