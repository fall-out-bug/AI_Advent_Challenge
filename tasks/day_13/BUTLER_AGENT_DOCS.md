# Butler Agent Documentation - Day 13

## Overview

Butler Agent is a production-ready Telegram bot that provides intelligent task management, channel digest generation, homework checking, and reminder services through natural language interaction.

## Architecture

### Hybrid Intent Recognition System

The Butler Agent uses a two-layer hybrid approach for intent classification:

1. **Rule-based Classification** (Layer 1)
   - Fast, synchronous regex pattern matching
   - High confidence threshold (≥0.85) for immediate results
   - Priority given to specific sub-intents over general mode intents

2. **LLM Classification** (Layer 2)
   - Fallback for complex or ambiguous queries
   - Uses Mistral-7B for semantic understanding
   - Cached results for performance optimization

3. **Caching Layer**
   - TTL-based cache (default: 300 seconds)
   - Reduces LLM calls for repeated queries
   - Automatically cleared when rule-based results differ

**Intent Types:**
- Mode-level: `TASK`, `DATA`, `REMINDERS`, `IDLE`
- Sub-intents: `TASK_CREATE`, `DATA_DIGEST`, `DATA_HW_STATUS`, `DATA_HW_QUEUE`, `DATA_HW_RETRY`, etc.

**Example Flow:**
```
User: "Дай полный статус домашних работ"
→ Rule-based: DATA_HW_STATUS (confidence: 0.99)
→ Direct routing to HW status handler
→ No LLM call needed
```

## MCP Tools

### Channel Management Tools

#### `add_channel`
Subscribe to a Telegram channel for digest generation.

**Parameters:**
- `user_id` (int): Telegram user ID
- `channel_username` (str): Channel username without @
- `tags` (list[str], optional): Annotation tags
- `title` (str, optional): Channel title metadata
- `description` (str, optional): Channel description metadata

**Returns:**
- `channel_id`: MongoDB document ID
- `status`: Subscription status

#### `list_channels`
List all subscribed channels for a user, with metadata enrichment.

**Parameters:**
- `user_id` (int): Telegram user ID

**Returns:**
- List of channels with `channel_username`, `title`, `description`, `tags`

**Features:**
- Automatically fetches missing metadata from Telegram API
- Updates database with fetched metadata

#### `remove_channel`
Unsubscribe from a channel.

**Parameters:**
- `user_id` (int): Telegram user ID
- `channel_username` (str): Channel username without @

#### `get_channel_metadata`
Get channel metadata (title, description) from database or Telegram API.

**Parameters:**
- `channel_username` (str): Channel username without @
- `user_id` (int, optional): Filter by user ID

**Returns:**
- Metadata dict with `title`, `description`, `tags`, `subscribed_at`

**Features:**
- First checks MongoDB for cached metadata
- If missing, fetches from Telegram API using Pyrogram
- Automatically saves fetched metadata to DB

### Channel Digest Tools

#### `get_channel_digest_by_name`
Generate digest for a specific channel by name/hint.

**Parameters:**
- `user_id` (int): Telegram user ID
- `channel_name_hint` (str): Channel name, username, or partial match
- `hours` (int, optional): Time period in hours (default: 168 = 7 days)

**Returns:**
- Digest dict with `channel_name`, `summary`, `post_count`, `hours`

**Features:**
- **Intelligent Channel Resolution**: Matches user input (e.g., "Набока") to actual channel (e.g., "onaboka")
  - Handles Russian declension normalization
  - Uses metadata (title, description) for matching
  - Scoring system for best match selection
- **Adaptive Summary Length**: Adjusts `max_sentences` based on filtered post count
- **Time-aware Filtering**: Only includes posts within requested time window
- **Automatic Data Collection**: Triggers post collection if no posts found

#### `get_channel_digest`
Generate digests for all subscribed channels.

**Parameters:**
- `user_id` (int): Telegram user ID
- `hours` (int, optional): Time period in hours (default: 168)

**Returns:**
- List of digest dictionaries

### Post Collection Tools

#### `collect_posts`
Manually trigger post collection for a channel.

**Parameters:**
- `user_id` (int): Telegram user ID
- `channel_username` (str): Channel username without @
- `hours` (int, optional): How far back to collect (default: 168)

**Returns:**
- Collection result with `posts_collected`, `posts_skipped`

### HW Checker Tools

The Butler Agent integrates with HW Checker MCP Server via HTTP client.

**Base URL:** `http://hw_checker-mcp-server-1:8005`

#### Available Operations

1. **Get All Checks Status** (`get_all_checks_status`)
   - Endpoint: `/api/all_checks_status`
   - Parameters: `assignment` (optional), `limit` (default: 100)
   - Returns: Full list of checks with all fields

2. **Get Queue Status** (`get_queue_status`)
   - Endpoint: `/api/queue_status`
   - Returns: Queue statistics and job list

3. **Retry Check** (`retry_check`)
   - Endpoint: `/api/retry_check`
   - Parameters: `job_id`, `archive_name`, or `commit_hash` (at least one required)
   - Returns: Retry job information

**Bot Commands:**
- "Дай полный статус домашних работ" → `DATA_HW_STATUS`
- "Покажи статус очереди" → `DATA_HW_QUEUE`
- "Перезапусти job_id {id}" → `DATA_HW_RETRY`

## Handler Architecture

### DataHandler

Handles all data-related requests:
- Channel subscriptions (`DATA_SUBSCRIPTION_ADD`, `DATA_SUBSCRIPTION_REMOVE`, `DATA_SUBSCRIPTION_LIST`)
- Digest generation (`DATA_DIGEST`)
- Student statistics (`DATA_STATS`)
- HW Checker operations (`DATA_HW_STATUS`, `DATA_HW_QUEUE`, `DATA_HW_RETRY`)

**Key Methods:**
- `_subscribe_to_channel`: Adds channel subscription with metadata
- `_unsubscribe_by_name`: Removes channel using intelligent name resolution
- `_list_channels`: Lists subscriptions with metadata enrichment
- `_get_channel_digest_by_name`: Generates digest with channel resolution
- `_get_hw_status`: Retrieves full homework status
- `_get_hw_queue_status`: Shows queue statistics
- `_retry_hw_submission`: Retries failed homework checks

### TaskHandler

Manages task creation, listing, updating, and deletion.

### RemindersHandler

Handles reminder creation, listing, and deletion.

### ChatHandler

Provides general conversation and question answering.

## Features

### Markdown Escaping

All user-facing messages are automatically escaped to prevent Telegram Markdown parsing errors:
- Escaped characters: `*`, `_`, `[`, `]`, `(`, `` ` ``, `)`
- Applied to: channel names, summaries, error messages, status texts

### Channel Resolution Logic

Intelligent matching of user-provided channel hints to actual subscribed channels:

1. **Exact Match**: Direct username match
2. **Case-insensitive Match**: Username without case sensitivity
3. **Metadata Match**: Searches in channel title and description
4. **Russian Declension**: Normalizes Russian endings (е → а, и → а)
5. **Word-based Matching**: Matches individual words from titles
6. **Scoring System**: Selects best match based on confidence score

**Example:**
```
User: "Дай дайджест Гладкова"
→ Searches channels with "Гладков" in title
→ Finds "alexgladkovblog" with title "Алексей Гладков"
→ Correctly resolves and generates digest
```

### Adaptive Summary Generation

- **Time-aware Prompts**: LLM receives time period context (e.g., "за последние 5 дней")
- **Adaptive Length**: `max_sentences` adjusted based on filtered post count
- **Post Filtering**: Only posts within requested time window are included
- **Fallback Heuristics**: Simple text extraction if LLM summarization fails

### Error Handling

- Graceful degradation for missing services (HW Checker, MongoDB)
- Retry mechanisms for transient failures
- Clear error messages for users
- Comprehensive logging for debugging

## Development

### Hotreload

See [README.HOTRELOAD.md](../../README.HOTRELOAD.md) for details.

**Quick Start:**
```bash
# Run with hotreload
docker-compose -f docker-compose.butler.yml -f docker-compose.butler.dev.yml up
```

### Testing

E2E tests cover full system flows:
- Chat mode responses
- Subscription management
- Channel addition/deletion
- Digest retrieval with channel resolution
- HW Checker operations

**Run tests:**
```bash
pytest tests/e2e/test_butler_agent_e2e.py -v
```

## Configuration

### Environment Variables

- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `MONGODB_URL`: MongoDB connection string
- `HW_CHECKER_BASE_URL`: HW Checker API base URL (default: `http://hw_checker-mcp-server-1:8005`)
- `LLM_BASE_URL`: Mistral API URL (default: `http://mistral:8000`)
- `TELEGRAM_SESSION_STRING`: Pyrogram session string for metadata fetching
- `TELEGRAM_API_ID`: Telegram API ID for Pyrogram
- `TELEGRAM_API_HASH`: Telegram API hash for Pyrogram

### Intent Classification

- `INTENT_CACHE_TTL`: Cache TTL in seconds (default: 300)
- `INTENT_CONFIDENCE_THRESHOLD`: Rule-based confidence threshold (default: 0.7)
- `INTENT_LLM_TIMEOUT`: LLM classification timeout in seconds (default: 5.0)

## Performance

- **Rule-based Classification**: <1ms latency
- **Cached Classification**: <2ms latency
- **LLM Classification**: ~500-2000ms latency (with timeout fallback)
- **Intent Metrics**: Prometheus metrics for classification performance

## Troubleshooting

### Bot Not Responding

1. Check container status:
   ```bash
   docker-compose -f docker-compose.butler.yml ps butler-bot
   ```

2. Check logs:
   ```bash
   docker-compose -f docker-compose.butler.yml logs butler-bot
   ```

3. Verify MCP server connectivity:
   ```bash
   docker-compose -f docker-compose.butler.yml exec butler-bot curl http://mcp-server:8004/health
   ```

### Intent Misclassification

1. Check rule patterns in `src/domain/intent/rules/`
2. Clear intent cache if needed
3. Check LLM timeout settings

### Channel Resolution Issues

1. Verify metadata is fetched: check MongoDB `channels` collection
2. Check Telegram API credentials for metadata fetching
3. Review channel resolution scoring in logs

### HW Checker Integration Issues

1. Verify HW Checker server is running:
   ```bash
   curl http://hw_checker-mcp-server-1:8005/health
   ```

2. Check `HW_CHECKER_BASE_URL` environment variable
3. Review HW Checker logs

## Future Improvements

- [ ] Support for multiple MCP servers (currently supports multiple HTTP MCP servers)
- [ ] Enhanced channel resolution with ML-based matching
- [ ] Batch operations for multiple channels
- [ ] Advanced digest customization (format, length, style)
- [ ] Scheduled digest delivery
- [ ] User preferences for intent classification thresholds

