<!-- 1e442ddc-251b-486c-b0ce-08642cc3a0c6 89e21593-4398-4893-bf2b-58b0bd37e9f7 -->
# PDF Digest System Implementation Plan - Day 12

## Architecture Overview

System collects posts hourly from subscribed Telegram channels, stores them in MongoDB with 7-day TTL, and generates PDF digests on-demand via MCP tools. Hybrid deduplication prevents duplicates based on message_id (24h window) and content_hash (7-day window).

## Phase 1: Post Storage Infrastructure (TDD)

### 1.1 Create PostRepository Tests First

**File**: `tests/infrastructure/repositories/test_post_repository.py` (new)

**TDD Approach**: Write tests first (Red phase), then implement (Green phase).

**Test Coverage** (80%+):

- Test `save_post` with deduplication by message_id
- Test `save_post` with deduplication by content_hash
- Test `save_post` saves new post successfully
- Test `get_posts_by_user_subscriptions` filters correctly
- Test `get_posts_by_channel` with date filtering
- Test `delete_old_posts` removes expired posts
- Test error handling for invalid inputs
- Test edge cases (empty lists, no subscriptions)

**Test Structure**: Arrange-Act-Assert pattern, use pytest fixtures for MongoDB setup.

### 1.2 Create PostRepository Implementation

**File**: `src/infrastructure/repositories/post_repository.py` (new)

**Code Quality Requirements** (AI Reviewer):

- Each method max 30-40 lines
- Single responsibility per method
- Google-style docstrings for all methods
- Type hints for all parameters and returns
- Extract deduplication logic to helper methods

**Methods** (max 30 lines each):

- `save_post(post: dict) -> str` - Save post with deduplication check
- `get_posts_by_user_subscriptions(user_id: int, hours: int) -> List[dict]` - Get posts for user's subscribed channels
- `get_posts_by_channel(channel_username: str, since: datetime) -> List[dict]` - Get posts for specific channel
- `_check_duplicate_by_message_id(channel_username: str, message_id: str, hours: int = 24) -> bool` - Private helper (max 15 lines)
- `_check_duplicate_by_content_hash(content_hash: str, days: int = 7) -> bool` - Private helper (max 15 lines)
- `delete_old_posts(days: int) -> int` - Cleanup old posts (max 20 lines)

**Deduplication Logic** (Hybrid - Option 3):

1. Check if `message_id` exists in last 24 hours for this `channel_username`
2. If not found, check `content_hash` (SHA256 of text + channel_username) in last 7 days
3. If duplicate found, skip; otherwise save with both `message_id` and `content_hash`

**MongoDB Schema**:

```python
{
    "_id": ObjectId,
    "channel_username": str,  # indexed
    "message_id": str,         # indexed (unique per channel in 24h window)
    "content_hash": str,       # SHA256(text + channel_username), indexed
    "user_id": int,            # indexed (for subscription filtering)
    "text": str,
    "date": datetime,          # indexed (for TTL and filtering)
    "fetched_at": datetime,
    "views": int | None,
    "metadata": {
        "edit_date": datetime | None,
        "media_type": str | None
    }
}
```

**Indexes**:

- `(channel_username, message_id)` - for quick message_id lookup
- `(content_hash, date)` - for content_hash deduplication
- `(user_id, date)` - for subscription-based queries
- `date` with TTL: 7 days (604800 seconds)

### 1.3 MCP Tool: save_posts_to_db (TDD)

**File**: `tests/presentation/mcp/test_digest_tools.py` (update)

**Add tests**:

- Test saving multiple posts
- Test deduplication logic
- Test error handling
- Test empty posts list

**File**: `src/presentation/mcp/tools/digest_tools.py` (update)

**Tool**: `save_posts_to_db(posts: List[dict], channel_username: str, user_id: int) -> Dict[str, Any]`

**Code Quality**: Max 30 lines, Google-style docstring with Args/Returns/Example/Raises.

**Purpose**: Save fetched posts to MongoDB via repository with deduplication.

**Returns**: `{"saved": int, "skipped": int, "total": int}`

### 1.4 Update fetch_channel_posts

**File**: `src/infrastructure/clients/telegram_utils.py` (update)

**Change**: After fetching posts, automatically save them via MCP tool `save_posts_to_db` if repository is available.

**Code Quality**: Refactor if function exceeds 40 lines, extract save logic to `_save_posts_to_db()` helper function.

**Documentation**: Update docstring with new behavior description.

## Phase 2: Post Fetcher Worker (TDD)

### 2.1 Create PostFetcherWorker Tests First

**File**: `tests/workers/test_post_fetcher_worker.py` (new)

**Test Coverage** (80%+):

- Test hourly schedule execution
- Test channel processing loop
- Test error handling (continue on channel failure)
- Test statistics logging
- Test MongoDB connection failures
- Test empty channels list

**Fixtures**: Mock MongoDB, MCP client, Telegram client.

### 2.2 Create PostFetcherWorker Implementation

**File**: `src/workers/post_fetcher_worker.py` (new)

**Code Quality Requirements**:

- Main class methods max 30-40 lines each
- Extract channel processing to `_process_channel()` method (max 30 lines)
- Extract error handling to `_handle_channel_error()` method (max 20 lines)
- Google-style docstrings for all methods

**Purpose**: Hourly collection of posts from all subscribed channels.

**Schedule**: Run every hour (cron: `0 * * * *`)

**Flow**:

1. Query MongoDB for all active channels (`channels` collection)
2. For each channel:

   - Call `fetch_channel_posts(channel_username, since=last_fetch_time or 1 hour ago)`
   - Call `save_posts_to_db(posts, channel_username, user_id)` via MCP
   - Update channel's `last_fetch` timestamp

3. Log statistics (posts saved, channels processed, errors)

**Error Handling**: Continue processing other channels if one fails.

**Integration**: Use same scheduler pattern as `summary_worker.py`.

**Monitoring** (DevOps):

- Add metrics: `post_fetcher_posts_saved_total` (Counter)
- Add metrics: `post_fetcher_channels_processed_total` (Counter)
- Add metrics: `post_fetcher_errors_total` (Counter)
- Add metrics: `post_fetcher_duration_seconds` (Histogram)
- Add alert: post fetcher fails > 3 times in 1 hour

### 2.3 Update digest_tools.get_channel_digest

**File**: `src/presentation/mcp/tools/digest_tools.py` (update)

**Change**: Replace direct `fetch_channel_posts` call with query to MongoDB via `PostRepository.get_posts_by_user_subscriptions`.

**Behavior**: Read posts from database instead of fetching from Telegram API.

**Code Quality**: Refactor if function exceeds 40 lines, extract database query to helper.

**Test**: Update existing tests to use mocked repository instead of mocked fetch_channel_posts.

## Phase 3: PDF Digest MCP Tools (TDD)

### 3.1 Tool: get_posts_from_db (TDD)

**File**: `tests/presentation/mcp/test_pdf_digest_tools.py` (new)

**Test Coverage**:

- Test posts grouping by channel
- Test limits (max 100 posts per channel, max 10 channels)
- Test empty results
- Test date filtering

**File**: `src/presentation/mcp/tools/pdf_digest_tools.py` (new)

**Tool**: `get_posts_from_db(user_id: int, hours: int = 24) -> Dict[str, Any]`

**Code Quality**: Max 30 lines, Google-style docstring with Args/Returns/Example/Raises.

**Purpose**: Retrieve posts from MongoDB grouped by channel.

**Returns**:

```python
{
    "posts_by_channel": {
        "channel1": [post1, post2, ...],
        "channel2": [post1, post2, ...]
    },
    "total_posts": int,
    "channels_count": int
}
```

**Limits**: Apply ML-engineer recommendations:

- Max posts per channel: 100 (to avoid token overflow)
- Max channels: 10 (from settings.digest_max_channels)

### 3.2 Tool: summarize_posts (TDD)

**File**: `tests/presentation/mcp/test_pdf_digest_tools.py` (add tests)

**Test Coverage**:

- Test summarization with various post counts
- Test limits enforcement (5-6 sentences, 3000 chars, 100 posts)
- Test LLM errors handling
- Test empty posts list
- Test token overflow handling

**File**: `src/presentation/mcp/tools/pdf_digest_tools.py` (add implementation)

**Tool**: `summarize_posts(posts: List[dict], channel_username: str, max_sentences: int = 5) -> Dict[str, Any]`

**Code Quality**: Max 30 lines, extract limit validation to `_validate_summary_limits()` helper function.

**Purpose**: Generate summary for posts from single channel using LLM.

**Limits** (ML-engineer recommendations):

- Max sentences per channel: 5-6 (decreased from 8 for better PDF readability)
- Max characters per summary: 3000 (increased from 2000 for PDF)
- Max tokens input: 3000 (within mistral/qwen recommended 3072)
- Max tokens output: 800 (for 5-6 sentences)
- Max posts for summarization: 100 per channel (if exceeded, take most recent 100)

**Returns**: `{"summary": str, "post_count": int, "channel": str}`

**Implementation**: Reuse existing `summarize_posts` function from `src/infrastructure/llm/summarizer.py` with adjusted parameters.

### 3.3 Tool: format_digest_markdown (TDD)

**File**: `tests/presentation/mcp/test_pdf_digest_tools.py` (add tests)

**Test Coverage**:

- Test markdown formatting
- Test metadata inclusion
- Test empty summaries handling
- Test multiple sections formatting

**File**: `src/presentation/mcp/tools/pdf_digest_tools.py` (add implementation)

**Tool**: `format_digest_markdown(summaries: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Dict[str, Any]`

**Code Quality**: Max 30 lines, extract template rendering to `_render_markdown_template()` helper function.

**Purpose**: Format channel summaries into markdown section.

**Input**: List of summaries from `summarize_posts`, metadata (generation_date, user_id, etc.)

**Output**:

```markdown
# Channel Digest
Generated: 2024-01-15 20:00 UTC
Channels: 5 | Total Posts: 42

## Channel 1
Summary text here...

## Channel 2
Summary text here...
```

**Returns**: `{"markdown": str, "sections_count": int}`

### 3.4 Tool: combine_markdown_sections (TDD)

**File**: `tests/presentation/mcp/test_pdf_digest_tools.py` (add tests)

**Test Coverage**:

- Test template rendering
- Test section combination
- Test different templates
- Test empty sections handling

**File**: `src/presentation/mcp/tools/pdf_digest_tools.py` (add implementation)

**Tool**: `combine_markdown_sections(sections: List[str], template: str = "default") -> Dict[str, Any]`

**Code Quality**: Max 30 lines, extract template loading to `_load_template()` helper function.

**Purpose**: Combine multiple markdown sections into single document with template.

**Template includes**:

- Header with date, user info (optional)
- Table of contents (optional)
- Sections
- Footer with metadata

**Returns**: `{"combined_markdown": str, "total_chars": int}`

### 3.5 Tool: convert_markdown_to_pdf (TDD)

**File**: `tests/presentation/mcp/test_pdf_digest_tools.py` (add tests)

**Test Coverage**:

- Test successful PDF conversion
- Test error handling (invalid markdown, missing dependencies)
- Test style variations
- Test large documents handling

**File**: `src/presentation/mcp/tools/pdf_digest_tools.py` (add implementation)

**Tool**: `convert_markdown_to_pdf(markdown: str, style: str = "default", metadata: Dict[str, Any] = None) -> Dict[str, Any]`

**Code Quality**: Max 40 lines, extract CSS generation to `_generate_css()`, PDF conversion to `_convert_to_pdf()`.

**Purpose**: Convert markdown to PDF using weasyprint.

**Dependencies**: Add `weasyprint` and `markdown` to `pyproject.toml`

**Styling**: Basic CSS styling for readability:

- Font: Arial/Helvetica, 12pt
- Headers: bold, larger font
- Section spacing
- Page breaks between major sections

**Returns**: `{"pdf_bytes": bytes (base64 encoded), "file_size": int, "pages": int}`

**Error Handling**: Return error dict if conversion fails.

**Monitoring** (DevOps):

- Add metric: `pdf_generation_duration_seconds` (Histogram)
- Add metric: `pdf_generation_errors_total` (Counter)
- Add metric: `pdf_file_size_bytes` (Histogram)

### 3.6 Register Tools

**File**: `src/presentation/mcp/server.py` (update)

**Change**: Add `pdf_digest_tools` to `tool_modules` list in `_register_all_tools()`.

## Phase 4: Bot Handler Update (TDD)

### 4.1 Update callback_digest Tests First

**File**: `tests/presentation/bot/test_menu_callbacks.py` (update)

**Add tests**:

- Test full PDF generation flow
- Test cache hit/miss
- Test error handling and fallback to text digest
- Test empty digest handling
- Test "no posts" message

**File**: `src/presentation/bot/handlers/menu.py` (update)

**Code Quality**: Refactor if function exceeds 40 lines, extract PDF generation flow to `_generate_pdf_digest()` helper function (max 30 lines).

**Flow**:

1. User clicks "Digest" button
2. Show `send_chat_action("upload_document")` immediately
3. Check cache first (1 hour TTL)
4. If not cached, call MCP tools in sequence:

   - `get_posts_from_db(user_id, hours=24)`
   - For each channel: `summarize_posts(posts, channel_username)`
   - `format_digest_markdown(summaries, metadata)`
   - `combine_markdown_sections(sections)`
   - `convert_markdown_to_pdf(combined_markdown, metadata)`

5. Cache PDF result
6. Send PDF via `bot.send_document(chat_id, pdf_bytes, filename="digest_YYYY-MM-DD.pdf")`

**Error Handling**:

- If PDF generation fails: fallback to existing `get_channel_digest` text format
- If no posts found: send message "No new posts in last 24 hours"
- If empty digest: send message "No digests available"

**Caching**: Cache PDF for 1 hour using key `f"digest_pdf:{user_id}:{date_hour}"` in memory or Redis (if available).

**Monitoring** (DevOps):

- Add metric: `bot_digest_requests_total` (Counter)
- Add metric: `bot_digest_cache_hits_total` (Counter)
- Add metric: `bot_digest_errors_total` (Counter)

### 4.2 Update menu.py imports

**File**: `src/presentation/bot/handlers/menu.py` (update)

**Add**: Import `MCPClient` if not already imported.

## Phase 5: Configuration Updates

### 5.1 Add Settings

**File**: `src/infrastructure/config/settings.py` (update)

**New fields**:

- `post_fetch_interval_hours: int = 1` - Post collection frequency
- `post_ttl_days: int = 7` - Post retention period
- `pdf_cache_ttl_hours: int = 1` - PDF cache duration
- `pdf_summary_sentences: int = 5` - Sentences per channel in PDF (separate from text digest)
- `pdf_summary_max_chars: int = 3000` - Max chars per channel summary in PDF
- `pdf_max_posts_per_channel: int = 100` - Max posts to summarize per channel

### 5.2 Update pyproject.toml

**File**: `pyproject.toml` (update)

**Add dependencies**:

- `weasyprint>=59.0` - PDF generation
- `markdown>=3.4` - Markdown parsing

## Phase 6: Testing (TDD Approach)

### 6.1 Unit Tests

**Files**:

- `tests/infrastructure/repositories/test_post_repository.py` (new)
- `tests/presentation/mcp/test_pdf_digest_tools.py` (new)
- `tests/workers/test_post_fetcher_worker.py` (new)
- `tests/presentation/bot/test_menu_callbacks.py` (update)

**TDD Process**: Write tests first (Red), implement to pass (Green), refactor (Refactor).

**Coverage Requirements** (QA/TDD Reviewer):

- PostRepository: 80%+ coverage, all edge cases
- PDF tools: 80%+ coverage, each tool independently
- Worker: 80%+ coverage, error handling, schedule logic
- Bot handler: 80%+ coverage, full flow, cache, error handling

**Test Structure**: Arrange-Act-Assert pattern, descriptive test names, use pytest fixtures.

### 6.2 Integration Tests

**File**: `tests/integration/test_pdf_digest_flow.py` (new)

**Test**: Full flow from post collection to PDF generation with real MongoDB.

**Requirements** (QA/TDD Reviewer):

- Use fixtures for setup/teardown
- Test cleanup after execution
- Include real services (MongoDB, MCP)
- Describe integration scenario
- Informative test logs

### 6.3 E2E Tests

**File**: `tests/e2e/test_digest_pdf_button.py` (new)

**Test**: Bot button click → PDF generation → file sent with mocked Telegram API.

**Requirements** (QA/TDD Reviewer):

- Isolated test environment
- Test data cleanup
- Expected results documented
- Runs in docker/compose environment

### 6.4 Contract Tests

**File**: `tests/contract/test_mcp_tools_schema.py` (update)

**Test**: Verify MCP tool schemas (input/output), backward compatibility.

**Requirements** (QA/TDD Reviewer):

- JSON/schema validation
- Test cases for different API versions
- Request/response structure validation

## Phase 7: Documentation (Technical Writer)

### 7.1 Docstrings

**Files**: All new files and updated files

**Requirements** (Technical Writer):

- Google-style docstrings for all functions/classes
- Include: Purpose, Args, Returns, Raises, Example
- English language, clear and concise
- No template comments, only meaningful documentation

### 7.2 README Updates

**File**: `README.md` and `README.ru.md` (update)

**Add sections**:

- PDF Digest feature description
- Quick start: how to generate PDF digest
- Configuration: new settings for PDF generation
- Troubleshooting: common PDF generation issues

### 7.3 API Documentation

**File**: `docs/day12/api.md` (new or update)

**Add**:

- MCP tools documentation (`get_posts_from_db`, `summarize_posts`, `format_digest_markdown`, `combine_markdown_sections`, `convert_markdown_to_pdf`)
- Request/response examples
- Error codes and handling
- Tool schemas

### 7.4 User Guide

**File**: `docs/day12/USER_GUIDE.md` (new or update)

**Add**:

- How to use PDF digest feature
- Button navigation guide
- PDF format description
- Troubleshooting section

### 7.5 CHANGELOG

**File**: `CHANGELOG.md` (update)

**Add entry** (semantic versioning):

```markdown
## [Unreleased] - Day 12
### Added
- PDF digest generation via MCP tools
- Post collection worker with hourly schedule
- Hybrid deduplication (message_id + content_hash)
- PDF caching (1 hour TTL)
- Prometheus metrics for post fetcher and PDF generation
### Changed
- Digest generation now reads from MongoDB instead of Telegram API
### Fixed
- [Any fixes]
```

### 7.6 Architecture Documentation

**File**: `docs/day12/ARCHITECTURE.md` (new)

**Add**:

- Post collection flow diagram (Mermaid)
- PDF generation flow diagram (Mermaid)
- Caching strategy
- Error handling strategy
- Database schema

## Phase 8: DevOps & Monitoring

### 8.1 Docker Compose Update

**File**: `docker-compose.day12.yml` (new, based on day11)

**Add**:

- `post-fetcher-worker` service with healthcheck
- Environment variables for worker configuration
- Dependencies (mongodb, mcp-server)
- Resource limits

### 8.2 Metrics & Monitoring

**Files**: Add metrics to workers and tools

**Metrics to add** (Prometheus-compatible):

- `post_fetcher_posts_saved_total` (Counter)
- `post_fetcher_channels_processed_total` (Counter)
- `post_fetcher_errors_total` (Counter)
- `post_fetcher_duration_seconds` (Histogram)
- `pdf_generation_duration_seconds` (Histogram)
- `pdf_generation_errors_total` (Counter)
- `pdf_file_size_bytes` (Histogram)
- `bot_digest_requests_total` (Counter)
- `bot_digest_cache_hits_total` (Counter)
- `bot_digest_errors_total` (Counter)

### 8.3 Alerts

**File**: `prometheus/alerts.yml` (create or update)

**Alerts** (DevOps Engineer):

- Post fetcher fails > 3 times in 1 hour (critical)
- PDF generation error rate > 10% in 5 minutes (warning)
- PDF generation latency > 30 seconds P95 (warning)

### 8.4 Health Checks

**Files**: Worker and service health checks

**Add**:

- Health check endpoint for post fetcher worker (`/health`)
- Health check for PDF generation service (if separate)
- MongoDB connection health check

### 8.5 Deployment Documentation

**File**: `docs/day12/DEPLOYMENT.md` (new)

**Add** (DevOps Engineer):

- How to deploy post fetcher worker
- Environment variables configuration
- Monitoring setup instructions
- Scaling considerations
- Docker Compose deployment guide

## Implementation Notes

### Code Quality Standards (AI Reviewer):

- **Function length**: Max 30-40 lines per function
- **Class responsibility**: Single responsibility principle
- **Docstrings**: Google-style for all public functions/classes
- **File size**: Split files > 2500 lines into logical modules
- **Token cost**: Keep functions < 2048 tokens for LLM readability
- **Naming**: Clear, descriptive names, consistent style

### ML-Engineer Limits Summary:

- **Summary per channel**: 5-6 sentences, max 3000 chars
- **Input tokens**: max 3000 per channel (within model limits)
- **Output tokens**: max 800 per channel
- **Posts per channel**: max 100 for summarization
- **Channels**: max 10 per digest
- **PDF cache**: 1 hour
- **Post retention**: 7 days (TTL)

### Deduplication Strategy:

1. Primary: `message_id` + `channel_username` (24h window) - fast lookup
2. Secondary: `content_hash` (SHA256) (7-day window) - catches edits/reposts
3. Implementation: Check message_id first, if not found check content_hash

### Error Recovery:

- PDF generation failure → fallback to text digest
- Empty digest → informative message
- Worker failure → log and continue with next channel
- MongoDB connection failure → retry with exponential backoff

### Testing Requirements (QA/TDD Reviewer):

- **Coverage**: 80%+ for all new code
- **TDD**: Write tests first, then implement (Red-Green-Refactor)
- **Test types**: Unit, Integration, E2E, Contract tests
- **Test structure**: Arrange-Act-Assert pattern
- **Fixtures**: Use pytest fixtures for setup/teardown
- **CI**: All tests run in CI pipeline

### Documentation Requirements (Technical Writer):

- **Docstrings**: Google-style with Purpose, Args, Returns, Raises, Example
- **README**: Feature description, quick start, configuration
- **API docs**: Request/response examples, error handling
- **CHANGELOG**: Semantic versioning format
- **User guide**: Step-by-step instructions

### DevOps Requirements (DevOps Engineer):

- **Metrics**: Prometheus-compatible metrics
- **Alerts**: Critical error rate and latency alerts
- **Health checks**: Service health endpoints
- **Docker**: Secure, minimal Dockerfiles
- **Deployment**: Documented deployment process
- **Monitoring**: Grafana dashboards (optional)

### To-dos

- [ ] Write unit tests for PostRepository (TDD - test first)
- [ ] Implement PostRepository with CRUD operations and hybrid deduplication (message_id + content_hash)
- [ ] Create MongoDB indexes and TTL (7 days) for posts collection
- [ ] Write tests for save_posts_to_db MCP tool
- [ ] Create MCP tool save_posts_to_db for saving fetched posts
- [ ] Update fetch_channel_posts to automatically save posts via repository, refactor if >40 lines
- [ ] Write tests for PostFetcherWorker (TDD - test first)
- [ ] Create PostFetcherWorker for hourly post collection from all subscribed channels
- [ ] Update get_channel_digest to read posts from MongoDB instead of Telegram API
- [ ] Write tests for get_posts_from_db MCP tool
- [ ] Create MCP tool get_posts_from_db to retrieve posts grouped by channel
- [ ] Write tests for summarize_posts MCP tool with ML-engineer limits
- [ ] Create MCP tool summarize_posts with ML-engineer limits (5-6 sentences, 3000 chars, 100 posts max)
- [ ] Write tests for format_digest_markdown MCP tool
- [ ] Create MCP tool format_digest_markdown to format summaries into markdown sections
- [ ] Write tests for combine_markdown_sections MCP tool
- [ ] Create MCP tool combine_markdown_sections with template and metadata
- [ ] Write tests for convert_markdown_to_pdf MCP tool
- [ ] Create MCP tool convert_markdown_to_pdf using weasyprint with basic styling
- [ ] Register pdf_digest_tools in MCP server
- [ ] Write tests for updated callback_digest handler (TDD - test first)
- [ ] Update callback_digest to generate PDF via MCP tools and send document with error handling, refactor if >40 lines
- [ ] Add PDF-related settings to Settings class (cache TTL, summary limits, etc.)
- [ ] Add weasyprint and markdown to pyproject.toml
- [ ] Write integration tests for full PDF digest flow
- [ ] Write E2E tests for bot button click → PDF generation → file sent
- [ ] Write contract tests for MCP tool schemas
- [ ] Add Google-style docstrings to all new functions/classes
- [ ] Update README.md with PDF digest feature description
- [ ] Add entry to CHANGELOG.md for Day 12 features
- [ ] Create/update API documentation in docs/day12/api.md
- [ ] Create/update user guide in docs/day12/USER_GUIDE.md
- [ ] Create architecture documentation in docs/day12/ARCHITECTURE.md with Mermaid diagrams
- [ ] Create docker-compose.day12.yml with post-fetcher-worker service
- [ ] Add Prometheus metrics for post fetcher and PDF generation
- [ ] Create Prometheus alert rules for critical errors
- [ ] Add health check endpoints for workers and services
- [ ] Create deployment documentation in docs/day12/DEPLOYMENT.md