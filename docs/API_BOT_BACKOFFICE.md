# Bot Backoffice CLI (EN)

Deterministic command-line interface that mirrors the Telegram digest/channel
flows without intent recognition. Owner-only usage.

## 1. Launching the CLI

```bash
poetry run python -m src.presentation.cli.backoffice.main <group> <command> [options]
```

- Default output: human-readable table.
- Add `--json` flag to receive machine-readable JSON.
- All commands require `--user-id` (Telegram user identifier used in the system).

## 2. Command Overview (Stage 02_02)

| Command | Description | Status |
|---------|-------------|--------|
| `channels list` | Show active subscriptions for a user | Ready |
| `channels add` | Subscribe user to a channel (validates via metadata) | Ready |
| `channels remove` | Mark subscription inactive | Ready |
| `digest run` | Generate digest for channel(s) | Ready |
| `digest last` | Inspect last digest timestamp & metadata | Ready |
| `channels refresh` | Trigger immediate post fetch | Backlog |
| `digest export` | Export digest to file (Markdown/PDF) | Backlog |
| `nlp test` | Run intent parsing sanity check | Optional |

## 3. Channel Commands

### 3.1 `channels list`

```bash
poetry run python -m src.presentation.cli.backoffice.main \
    channels list --user-id 12345 [--limit 50] [--json]
```

- Default: table with columns `id`, `channel`, `title`, `tags`, `active`, `subscribed_at`.
- JSON mode returns list of channel objects.
- `--limit` caps result count (default 100, max 500).

### 3.2 `channels add`

```bash
poetry run python -m src.presentation.cli.backoffice.main \
    channels add --user-id 12345 --channel tech_news [--tag analytics] [--json]
```

- Validates channel metadata (via Telegram API) before persisting.
- Tags supplied via repeated `--tag` flags.
- Exit codes: `0` success / already subscribed, `1` validation error.

### 3.3 `channels remove`

```bash
poetry run python -m src.presentation.cli.backoffice.main \
    channels remove --user-id 12345 --channel-id 507f1f77bcf86cd799439011 [--json]
```

- Marks subscription inactive. Output includes `status` and `channel_id`.

### 3.4 `channels refresh`

> Planned for post-MVP. Command remains documented for backlog alignment.

```bash
poetry run python -m src.presentation.cli.backoffice.main \
    channels refresh --user-id 12345 --channel-id 507f... [--hours 72]
```

- Will enqueue immediate fetch job; not yet implemented in Stage 02_02.

## 4. Digest Commands

### 4.1 `digest run`

```bash
poetry run python -m src.presentation.cli.backoffice.main \
    digest run --user-id 12345 [--channel tech_news] [--hours 24] \
    [--format markdown|json] [--json]
```

- When `--channel` omitted, generates digests for all active subscriptions.
- `--format markdown` returns plain summary text; `json` includes summary metadata.
- JSON output wraps entries in a list with fields `channel`, `summary`, `post_count`, etc.

### 4.2 `digest last`

```bash
poetry run python -m src.presentation.cli.backoffice.main \
    digest last --user-id 12345 --channel tech_news [--json]
```

- Displays stored metadata (`last_digest` timestamp, tags, active flag).
- Non-zero exit code when channel not found.

## 5. NLP Command (Optional)

```
poetry run python -m src.presentation.cli.backoffice.main \
    nlp test --user-id 12345 --text "show digest for tech news"
```

Useful for validating slot-filling or regression tests.

## 6. Implementation Notes

- CLI currently reuses existing MCP tool implementations (Stage 02_01) for subscription lifecycle.
- Prometheus metrics exported via `cli_command_total`, `cli_command_duration_seconds`,
  and `cli_command_errors_total`.
- Authentication: owner-only; environment variables / config drive DB & API credentials.
- Future enhancements: batch imports (`csv`), tagging utilities, digest scheduling, PDF export.

## 7. Localization

- CLI output uses Russian defaults (summary text comes from summariser). Documentation mirrored in RU version (`docs/API_BOT_BACKOFFICE.ru.md`).

