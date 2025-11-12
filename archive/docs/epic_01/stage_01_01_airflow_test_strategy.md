# EP01 Stage 01_01 · Airflow Test Infrastructure Analysis

| Option | Description | Pros | Cons | Estimated Runtime Impact | Maintenance Cost | Dependencies / Notes |
|--------|-------------|------|------|--------------------------|------------------|----------------------|
| A | Provision lightweight Airflow service in CI (docker-compose or ephemeral container). | - True integration coverage (no behavioural drift)<br>- Matches existing fixtures | - CI setup complexity<br>- Longer pipeline runtime<br>- Requires Airflow image upkeep | +6–10 min per pipeline (startup + test execution) | Medium/High (tracking Airflow updates, security patches) | Needs infra SME to confirm available base image and resource constraints. |
| B | Replace Airflow-dependent tests with targeted mocks/stubs covering DAG logic. | - Minimal CI impact<br>- No extra infra<br>- Easier local runs | - Lower fidelity (may miss operator-level regressions)<br>- Requires careful test redesign | +0–1 min (unit-level) | Medium (initial engineering effort; low ongoing) | Requires deep dive with Airflow subject-matter expert to ensure critical paths are mocked correctly. |
| C | Hybrid: keep small smoke test suite via Airflow container, mock the rest. | - Balances fidelity and runtime<br>- Limits container usage | - Need to curate smoke list<br>- Complexity in test split | +3–4 min | Medium | Define smoke scope with SMEs; ensures coverage of most critical DAGs only. |

## SME Questions

1. What is the minimal Airflow image/config we can run within CI resource limits?
2. Which DAGs/tests are critical for Stage 01_02 readiness (inputs to Option C)?
3. Are there existing scripts for seeding Airflow state that we can reuse?
4. Who owns Airflow version updates if Option A or C proceeds?

Next Steps:
- Circulate this matrix to infra team for input.
- Record decision in Stage 01_02 planning once SME responses are collected.

