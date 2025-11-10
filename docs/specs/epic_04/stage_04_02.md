# Stage 04_02 · Migration Execution

## Goal
Carry out the archival plan by relocating, deprecating, or deleting legacy
assets while preserving repository stability.

## Checklist

## Deliverables
- Pull requests or change sets executing the migrations.
- Updated documentation indicating new locations or removal notices.
- Migration log appended to stage summary.
- IaC assets for Grafana dashboards and updated Alertmanager/Loki rules merged
  with validation evidence.

## Metrics & Evidence
- CI run showing green status post-migration.
- Repository diff verifying only planned assets affected.
- Search report confirming legacy references resolved.
- Executed `observability-checks` workflow (or equivalent) validating new Grafana
  provisioning and Loki alerts.
- Migration log capturing archived documents and scripts.

## Dependencies
- Stage 04_01 approval and communication plan.
- Coordination with EP02/EP03 where codepaths intersect.
- Access to documentation maintainers for quick updates.

## Exit Criteria
- All scoped assets migrated/removed with sign-offs captured.
- CI/tests green; no unresolved references or import errors.
- Migration log shared with stakeholders and stored alongside archive README.

## Open Questions
- Do we maintain compatibility shims for a deprecation window?
- Are additional metadata (e.g., README in each archive folder) required now or
  in Stage 04_03?

## Remediation Overview

### Common Issues
1. **Missing Dependencies**: Ensure all required dependencies are installed and
   accessible.
2. **Incorrect Naming**: Double-check asset names and paths to ensure they
   match the new structure.
3. **Broken Links**: Verify that all external references (e.g., imports,
   documentation) are updated correctly.
4. **Permission Issues**: Ensure the user running the migration has the
   necessary permissions for file operations.
5. **CI/Test Failures**: Investigate and fix any test failures that occur
   during the migration process.

### Troubleshooting Steps
1. **Check CI/Test Logs**: Review the CI/test logs for any errors or
   warnings.
2. **Verify File Existence**: Manually check if the files you expect to
   migrate/delete actually exist.
3. **Check Permissions**: Use `ls -l` to verify file permissions.
4. **Update References**: Use a search tool (e.g., `grep -r`) to find
   remaining references to the old asset.
5. **Rollback Plan**: Have a clear plan for how to revert the changes if
   something goes wrong.

### Best Practices
1. **Atomic Operations**: Perform each migration as a single, atomic
   operation.
2. **Dry Run**: Always perform a dry run (e.g., `git diff`) to verify
   changes before committing.
3. **Documentation**: Document the migration process thoroughly, including
   any manual steps.
4. **Testing**: Ensure comprehensive testing (CI/tests) before
   production deployment.
5. **Observability**: Continuously monitor the system for any
   unexpected behavior.

## Preparation

- Stage 04_01 sign-off requests sent 2025-11-09 (see `signoff_log.md`)
- Remediation waves defined in `remediation_plan.md`
- Archive structure and evidence bundle prepared for migrations
- Shared infra dependency documented (`docs/specs/operations.md`) with helper script `scripts/infra/start_shared_infra.sh`
- CLI `digest:export` command implemented to replace PDF MCP tooling (`src/presentation/cli/backoffice/commands/digest.py`)

## Migration Log

- Archived legacy scripts (`start_models.sh`, `wait_for_model.sh`, `check_model_status.sh`, `ci/test_day10.sh`, `day12_run.py`, `mcp_comprehensive_demo.py`, `healthcheck_mcp.py`) and removed `telegram_channel_reader.session`
- Added stubs pointing to shared infra workflows and updated archive manifest/readmes
- Re-ran `poetry run pytest packages/multipass-reviewer -q`; evidence stored under `docs/specs/epic_04/evidence/test_baseline_packages_multipass_reviewer_2025-11-09T112856Z.txt`
- Updated shared infra connectivity tests to fail fast with actionable guidance when services are down; captured command `scripts/infra/start_shared_infra.sh`
- Added CLI digest export path (`digest:export`) and backing service module (`digest_exporter`); PDF generation now handled outside MCP
- Archived PDF digest MCP module and associated tests; CLI export is canonical
- Refactored homework review MCP tool to modular reviewer workflow; removed deprecation flag
- Removed legacy orchestration adapter; MCPApplicationAdapter chains generation and review adapters
- Archived legacy message sender; summary worker owns retry logic for digests
- Retired reminders dialog mode; Butler orchestrator routes legacy requests to chat and archived handler
- Migrated Butler legacy usecases to `src/application/use_cases/`; archived `src/application/usecases/`
- Introduced presentation-layer Butler orchestrator and handlers; domain agents now eligible for archival
- Removed `tests/integration/test_mcp_comprehensive_demo.py`; added backoffice CLI help coverage under `tests/integration/presentation/cli/test_backoffice_cli.py`
- Documented shared infra bootstrap in README; replaced local model scripts with `scripts/infra/start_shared_infra.sh`

## Validation Summary

- ✅ `poetry run pytest src/tests/infrastructure/monitoring/test_prometheus_metrics.py -q`
- ✅ `poetry run pytest tests/integration/presentation/cli/test_backoffice_cli.py -q`
- ✅ `MONGODB_URL="mongodb://admin:<pwd>@127.0.0.1:27017/butler_test?authSource=admin" poetry run pytest -q`
  - Result: **429 passed / 2 xfailed** (latency benchmarks intentionally xfail)
  - Evidence: `docs/specs/epic_04/evidence/test_summary_stage_04_03_final_2025-11-10T2358Z.txt`
  - Requirement: shared infra running via `~/work/infra/scripts/start-infra.sh` and `MONGO_PASSWORD` sourced from `.env.infra`
- Decision: Stage 04_02 validation complete; latency benchmark recalibration remains tracked in Stage 04_03/known issues.
