# Stage 05_03 Governance Policy · Fine-Tuning Lifecycle

## Purpose
Define approval, safety, and rollback expectations for fine-tuning cycles that
reuse datasets produced in Stage 05_02. This policy applies to RU summarisation
models released alongside main product versions.

## Roles & Approvals
- **Initiator (ML Engineer):** prepares pilot plan, data cards, and executes jobs.
- **Reviewer (ML Lead):** validates dataset quality, prompt versions, and approves
  fine-tuning launch.
- **Operations Owner:** confirms observability coverage, release scheduling,
  and rollback readiness.
- **Stakeholders:** sign-off stored in `docs/specs/epic_05/stage_05_03_signoff.md`.

No external compliance/legal approval required prior to production deployment.
Fine-tuning releases align with main release cadence (minor/major tags).

## Safety Checks
1. **Dataset Validation**
   - Confirm datasets exported via Stage 05_02 pipelines for target locale.
   - Check schema compliance and absence of PII.
2. **Baseline Benchmark**
   - Run dry-run benchmark (`scripts/benchmark/run_benchmark.py --dry-run`) and
     record metrics.
3. **Training Configuration Review**
   - Document model, hyperparameters, and compute in pilot plan.
   - Ensure reproducibility (seed, git commit, dataset hash).

## Execution Workflow
1. Submit pilot request with dataset snapshot (Stage 05_02 exports; see
   `stage_05_03_pilot.md`) and plan.
2. Collect approvals from ML Lead and Operations Owner.
3. Execute fine-tuning job per runbook.
4. Evaluate post-training metrics (Stage 05 benchmark plus additional drift
   metrics) and compare vs baseline thresholds.
5. Decide go/no-go; document in pilot report.

## Rollback Strategy
- Maintain previous model artefacts and configs in registry.
- If evaluation fails or regressions detected, switch deployment pointer back to
  baseline model; re-run benchmarks to confirm recovery.
- Log incident and root cause in runbook appendix.

## Monitoring Requirements
- Track latency, accuracy, coverage, and drift metrics via Prometheus/Grafana.
- Alert thresholds inherited from Stage 05_02; configure new alerts when metrics
  fall below acceptance bands post-release.

## Documentation Artifacts
- Governance policy (this document) stored under `docs/specs/epic_05/`.
- Pilot plan/report, runbook, and sign-off logs referenced from the Stage 05_03
  summary.

Keep policy updated alongside future epics when scope or approval matrix changes.
