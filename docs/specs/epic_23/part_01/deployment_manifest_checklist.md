# Epic 23 · Deployment Manifest Checklist

**Purpose:** Track legacy asset purging and deployment hygiene tasks as part of TL-06 documentation and localization efforts.

## Legacy Assets Purge Checklist

| Item | Location | Status | Notes |
|------|----------|--------|-------|
| Legacy async tests with `LegacyDialogContextAdapter` | `tests/legacy/epic21/test_butler_orchestrator_integration.py`, `tests/legacy/epic21/test_use_case_decomposition_integration.py` | ✅ Archived | Legacy tests preserved in `tests/legacy/epic21/` for reference; documented in `archive/docs/epic_21/epic_21_backlog.md` |
| Compressed large JSONL files | `results_stage20.jsonl.gz`, `results_with_labels.jsonl.gz` | ✅ Compressed | Files compressed from 555KB to ~148KB (26.5% of original); original files retained for compatibility |
| Invalid YAML/JSON files | `config/mcp_config.yaml`, `tests/e2e/telegram/fixtures/test_messages.json`, `archive/docker-compose/docker-compose.yml` | ✅ Fixed | All files validated and corrected |
| Lint issues in shared/tests | `shared/tests/test_agents.py`, `shared/tests/test_api_keys.py`, `shared/tests/test_external_apis.py` | ✅ Fixed | Black formatted, unused imports removed |

## Deployment Verification

### Pre-deployment Checks
- [x] All YAML/JSON files validated
- [x] Lint issues resolved (`make lint` passes)
- [x] Large data files compressed (<500KB)
- [x] Legacy tests documented in backlog
- [x] RU/EN documentation updated with observability info

### Post-deployment Checks
- [ ] Verify compressed files can be decompressed
- [ ] Verify legacy test references are properly documented
- [ ] Confirm no broken references to purged assets
- [ ] Verify README.ru.md and README.md reflect latest changes

## Asset Inventory

### Compressed Files
- `results_stage20.jsonl.gz` (compressed from 555KB)
- `results_with_labels.jsonl.gz` (compressed from 555KB)

### Archived Legacy Tests
- `tests/legacy/epic21/test_butler_orchestrator_integration.py` (uses `LegacyDialogContextAdapter`)
- `tests/legacy/epic21/test_use_case_decomposition_integration.py` (legacy integration tests)

### Documentation Updates
- `README.ru.md` - Added observability and restart validation sections
- `README.md` - Added large data files section
- `archive/docs/epic_21/epic_21_backlog.md` - Added legacy async tests archive entry

## Sign-off
- **Dev A**: _dev_a (2025-11-16)_
- **Tech Lead**: _pending_
