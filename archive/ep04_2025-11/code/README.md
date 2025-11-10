# EP04 Archive · Code Assets

List archived application modules here with a short rationale and replacement reference. Mirror entries with `ARCHIVE_MANIFEST.md` and include any setup notes required to run the legacy code in isolation.
- `src/presentation/mcp/tools/pdf_digest_tools.py` — superseded by CLI `digest:export` workflow
- `src/presentation/mcp/adapters/orchestration_adapter.py` — legacy multi-agent pipeline; MCPApplicationAdapter now performs sequential generate+review via modular reviewer
- `src/workers/message_sender.py` — legacy retry helper; summary worker now owns notification pipeline
- `src/application/usecases/` — legacy Butler task/data use cases archived after migration to `use_cases/`
