# Bot Backoffice CLI (EN)

Deterministic command-line interface that mirrors the Telegram digest/channel
flows without intent recognition. Owner-only usage.

## 1. Installation

CLI will live under `src/presentation/cli/backoffice/` (work in progress).
For now the specification defines command surface for upcoming implementation.

## 2. Command Overview

| Command | Description | Status |
|---------|-------------|--------|
| `channels list` | Show active subscriptions | Planned |
| `channels add` | Subscribe to a channel | Planned |
| `channels remove` | Unsubscribe from channel | Planned |
| `channels refresh` | Trigger immediate fetch | Planned |
| `digest run` | Generate digest for channel | Planned |
| `digest last` | Inspect last digest metadata | Planned |
| `nlp test` | Run intent parsing sanity check | Optional |

All commands accept `--output json` to emit machine-readable payloads.
Default format is human-friendly table/markdown.

## 3. Channel Commands

### 3.1 `channels list`

```
butler-cli channels list [--limit N] [--include-tags] [--output json]
```

Response (table or JSON):

| Channel | Title | Tags | Active | Since |
|---------|-------|------|--------|-------|

### 3.2 `channels add`

```
butler-cli channels add --username <name> [--tags t1,t2]
```

Return codes:

- `0` subscription added
- `1` validation error (channel not found, already subscribed)

### 3.3 `channels remove`

```
butler-cli channels remove (--channel-id <id> | --username <name>)
```

Outputs status string (`removed`, `not_found`).

### 3.4 `channels refresh`

```
butler-cli channels refresh (--channel-id <id> | --username <name>) [--hours 24]
```

Schedules fetch job via MCP or worker queue; prints job identifier.

## 4. Digest Commands

### 4.1 `digest run`

```
butler-cli digest run --channel <name> [--hours 24] [--format markdown|json]
```

Returns digest summary (markdown by default).
JSON format contains the same fields as `digest_generate`.

### 4.2 `digest last`

```
butler-cli digest last --channel <name>
```

Displays timestamp, post count, short summary.

## 5. NLP Command (Optional)

```
butler-cli nlp test --text "show digest for tech news"
```

Useful for validating slot-filling or regression tests.

## 6. Implementation Notes

- CLI should reuse MCP tools (`API_MCP.md`) under the hood.
- Logging should include `trace_id` or command UUID.
- Authentication: owner-only; initial version relies on env vars / local config.
- Future enhancements: batch imports (`csv`), tagging utilities, digest scheduling.

## 7. Localization

- Default CLI output Russian (`--lang en` optional).
- Command help text must be available in EN/RU via `API_BOT_BACKOFFICE.ru.md`.

