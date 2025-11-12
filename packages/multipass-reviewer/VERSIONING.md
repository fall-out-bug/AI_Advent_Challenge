`multipass-reviewer` follows [Semantic Versioning](https://semver.org/) and a documentation-first release workflow.

## Version scheme
- **MAJOR**: Breaking API changes (contract updates for domain/application interfaces).
- **MINOR**: Backwards-compatible feature work, new checkers/passes, observability improvements.
- **PATCH**: Bug fixes, documentation-only updates, or tooling changes that keep behaviour identical.

All code must land through PRs that update `pyproject.toml` and append a `CHANGELOG.md` entry for the release.

## Release checklist
1. Ensure `poetry lock` is up to date and CI passes (lint, tests, coverage ≥90%).
2. Update `pyproject.toml` with the new semantic version.
3. Document the release in `CHANGELOG.md` (date in UTC, bullet list of highlights).
4. Tag the repository (`git tag vX.Y.Z && git push --tags`).
5. Publish the package (`poetry build` + upload, or CI equivalent).

## Release history
- **0.2.0 (2025-11-08)** — LLM retry with Tenacity, graceful degradation for partial reports, expanded metrics.
- **0.1.0 (2025-11-07)** — Initial Clean Architecture scaffolding and core passes/checkers.
