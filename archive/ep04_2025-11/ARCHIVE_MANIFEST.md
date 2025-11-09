# EP04 · November 2025 Archive Manifest

## Purpose

This manifest tracks every asset moved into `archive/ep04_2025-11` during Epic 04 Stage 04_02. Use it as the single source of truth for retrieval, replacements, and approvals.

## Structure

```
archive/ep04_2025-11/
├── code/
│   └── README.md
├── docs/
│   └── README.md
├── scripts/
│   └── README.md
├── tests/
│   └── README.md
└── ARCHIVE_MANIFEST.md
```

## Entry Format

Each archived asset must be appended to the table below with:

- Original repository path
- New archive location (relative to `archive/ep04_2025-11/`)
- Successor or replacement reference
- Archive date (YYYY-MM-DD)
- Archived by (owner)
- Sign-off stakeholders

| Original Path | Archive Location | Replacement / Notes | Date | Archived By | Sign-offs |
|---------------|------------------|---------------------|------|-------------|-----------|
| _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |

## Process Checklist

1. Confirm asset appears in `docs/specs/epic_04/archive_scope.md`.
2. Ensure dependencies resolved or documented in `dependency_map.md`.
3. Move files to appropriate subfolder (`code/`, `docs/`, `scripts/`, `tests/`).
4. Update subfolder `README.md` with context.
5. Append manifest entry and capture approvals in `docs/specs/progress.md`.

## Retrieval Guidance

- Archived assets remain readable but should not be imported or executed.
- For rollbacks, copy files back to active locations via PR with stakeholder approval.
- Keep archive immutable after Stage 04_02 unless incident response requires adjustments.
