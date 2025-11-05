# E2E Tests for Summarization System

## Overview

End-to-end tests for the summarization system that use real services:
- MongoDB (test database)
- LLM service (local or remote)
- Telegram API (optional, for channel testing)

## Prerequisites

### 1. Services Running

- **MongoDB**: `make mongo-up` or MongoDB running on localhost:27017
- **LLM Service**: `make day-12-up` or LLM service available at configured URL

### 2. Environment Variables

Create `.env.test` file:

```bash
# E2E Test Configuration
TEST_MONGODB_URL=mongodb://localhost:27017
TEST_LLM_URL=http://localhost:8001
TEST_CHANNEL_USERNAME=your_test_channel
TEST_USER_ID=12345

# Optional: Telegram API credentials (for channel testing)
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
```

### 3. Test Telegram Channel Setup

1. Create a private Telegram channel for testing
2. Add your bot as administrator
3. Publish 10-15 test posts with diverse content
4. Set `TEST_CHANNEL_USERNAME` environment variable

## Running Tests

### Run all E2E tests:
```bash
pytest -m e2e tests/e2e/summarization/
```

### Run specific test:
```bash
pytest tests/e2e/summarization/test_real_digest_generation.py::test_generate_real_channel_digest
```

### Run with verbose output:
```bash
pytest -v -s tests/e2e/summarization/
```

## Test Structure

- `conftest.py`: Shared fixtures for real services
- `test_real_digest_generation.py`: Tests for digest generation with real LLM
- `test_performance.py`: Performance benchmarks

## Troubleshooting

### LLM Service Unavailable
- Check if LLM service is running: `curl http://localhost:8001/health`
- Verify `TEST_LLM_URL` environment variable
- Tests will be skipped if LLM unavailable

### MongoDB Connection Issues
- Verify MongoDB is running: `docker ps | grep mongo`
- Check `TEST_MONGODB_URL` environment variable
- Ensure test database is accessible

### Test Channel Not Found
- Verify channel username is correct (without @)
- Ensure bot is added as administrator
- Check channel has recent posts

## Test Data Management

Tests automatically clean up test data marked with `test_data: true`.
Make sure to use test markers when creating data in tests.
