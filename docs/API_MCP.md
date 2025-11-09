# MCP Tool API (EN)

The Butler MCP server now exposes only supported digest, channel, and NLP tools
by default. Deprecated and archived tools remain discoverable only when the
`MCP_INCLUDE_DEPRECATED_TOOLS=1` flag is enabled on both the server and the
client. Each discovery response now includes tool `status` metadata that callers
must respect.

> **Stage 01_03 (0.3.0):** Modular reviewer tools are always enabled; removal of the `use_modular_reviewer` flag means MCP deployments should assume the reviewer pipeline is active when CI is green.

## 1. Discovery Overview

- Use `MCPToolsRegistry.discover_tools()` to obtain the filtered catalogue.  
- Tool metadata contains `status` (`supported`, `transition`, `deprecated`,
  `archived`) and an optional migration note.  
- Deprecated/archived tools are hidden unless the opt-in flag is set.

```python
from src.presentation.mcp.client import MCPClient
from src.presentation.mcp.tools_registry import MCPToolsRegistry

client = MCPClient()
registry = MCPToolsRegistry(client)
tools = await registry.discover_tools()

for tool in tools:
    print(tool.name, tool.status, tool.note)
```

## 2. Supported Tools

| Tool Name | Module | Purpose | Notes |
|-----------|--------|---------|-------|
| `parse_digest_intent` | `nlp_tools.py` | Parse natural language digest requests | Keeps CLI/bot in sync with RU localisation. |
| `get_channel_digest_by_name` | `channels/channel_digest.py` | Generate digest for a specific channel | Uses modular summarisation pipeline. |
| `get_channel_digest` | `channels/channel_digest.py` | Generate digest for all active subscriptions | Supports new summarisation use case. |
| `request_channel_digest_async` | `channels/channel_digest.py` | Enqueue long-running digest job | Worker integration preserved. |
| `get_channel_metadata` | `channels/channel_metadata.py` | Resolve channel metadata from Mongo/Telegram | Provides data to CLI and bot flows. |
| `resolve_channel_name` | `channels/channel_resolution.py` | Fuzzy channel lookup for user input | Falls back to Telegram search when allowed. |

### 2.1 `get_channel_digest`

**Args**

```json
{
  "user_id": 12345,
  "hours": 24
}
```

**Response**

```json
{
  "digests": [
    {
      "channel": "tech_news",
      "summary": "Summary text…",
      "post_count": 5,
      "tags": ["analytics"]
    }
  ],
  "generated_at": "2025-11-09T11:00:00Z"
}
```

### 2.2 `get_channel_metadata`

**Args**: `{ "channel_username": "tech_news", "user_id": 12345 }`  
**Response**: Metadata dictionary with `title`, `description`, `success` flag, and
lookup notes. Falls back to Telegram search when Mongo data is stale.

### 2.3 `parse_digest_intent`

**Args**: `{ "text": "нужен дайджест за последние 24 часа", "user_context": {} }`  
**Response**: Intent payload containing `intent_type`, `confidence`, inferred
`hours`, optional `questions`, and recommended tool sequence.

## 3. Transition Tools (Moving to CLI Backoffice)

These tools remain callable for backward compatibility but will be replaced by
Stage 02_02 CLI commands. Consumers should migrate to the CLI equivalents listed
in the migration bulletin.

| Tool Name | Purpose | Planned Replacement |
|-----------|---------|----------------------|
| `add_channel` | Subscribe user to a channel | `cli channels add` |
| `list_channels` | List active subscriptions | `cli channels list` |
| `delete_channel` | Remove subscription | `cli channels remove` |
| `get_posts` | Read recent posts from Mongo | `cli channels refresh --dry-run` |
| `collect_posts` | Harvest posts via Telegram | `cli channels refresh` |
| `save_posts_to_db` | Persist harvested posts | CLI ingestion pipeline |

> **Note:** Transition tools continue to require Mongo and Telegram credentials.
> Their responses remain unchanged until Stage 02_02 completes.

## 4. Deprecated Tools (Opt-In Only)

Deprecated tools register only when `MCP_INCLUDE_DEPRECATED_TOOLS=1`. Each call
emits a structured deprecation warning.

| Tool Name | Status Note |
|-----------|-------------|
| `review_homework_archive` | Replaced by modular reviewer tool after EP01. |
| `get_posts_from_db` | PDF digest flows superseded by CLI export. |
| `summarize_posts` | CLI summariser handles channel summaries. |
| `format_digest_markdown` | Markdown formatting moves to CLI renderer. |
| `combine_markdown_sections` | CLI template combines sections. |
| `convert_markdown_to_pdf` | PDF export handled outside MCP. |

## 5. Archived Tools (Retiring)

These tools are no longer exposed by default and will be removed during the EP04
archival sweep. Avoid all new dependencies.

| Tool Name | Rationale |
|-----------|-----------|
| `add_task`, `list_tasks`, `update_task`, `delete_task`, `get_summary` | Reminder/task flows discontinued. |
| `parse_task_intent` | Reminder intent detection path removed. |

## 6. Error Model

All tools return structured results. Errors follow the envelope:

```json
{
  "status": "error",
  "error": "human-readable message",
  "details": { "context": "optional diagnostic payload" }
}
```

Common errors:

- `invalid_user_id`
- `channel_not_found`
- `digest_unavailable`
- `nlp_timeout`

## 7. Health & Monitoring

- MCP HTTP endpoint: `GET /health` → `{"status": "ok"}`  
- Prometheus metrics exposed when shared infra is configured.  
- Deprecated tool usage is logged with `WARNING` level and tool name.

## 8. Related Documents

- `docs/specs/epic_02/mcp_tool_matrix.md` — definitive catalogue.  
- `docs/specs/epic_02/mcp_migration_bulletin.md` — migration guidance & CLI mapping.  
- `docs/CHANGELOG_MCP.md` — public changelog of MCP tooling updates.  
- `docs/API_MCP.ru.md` — Russian localisation of this document.  
- `docs/API_BOT_BACKOFFICE.md` — CLI command reference (Stage 02_02).  

