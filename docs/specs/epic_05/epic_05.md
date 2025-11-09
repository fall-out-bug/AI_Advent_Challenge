# Epic 05 · Summarisation & Fine-Tuning Roadmap

## Purpose
Extend the summarisation pipeline and establish a controlled fine-tuning loop
that leverages high-quality reviewer outputs, aligning with Day 15+ ambitions.

## Objectives
- Define benchmark methodology, datasets, and evaluation metrics for
  summarisation quality across supported languages.
- Automate LLM-as-judge evaluations and dataset curation pipelines.
- Design governance for fine-tuning loops, including approval workflows, safety
  gates, and monitoring.

## Activation Note
This epic may run in parallel with EP01–EP04 if capacity allows; otherwise it
should start once reviewer hardening (EP01) and observability improvements
(EP03) provide stable foundations.

## Dependencies
- EP01 metrics/logging hooks for reviewer outputs.
- EP03 observability stack for tracking benchmark runs and fine-tuning jobs.
- Shared infra (LLM API, storage) for dataset processing.

## Stage Breakdown
| Stage | Scope | Key Deliverables | Exit Criteria |
|-------|-------|------------------|---------------|
| Stage 05_01 | Benchmark & dataset design | Benchmark plan, dataset schema, sampling strategy | Plan approved, datasets seeded, evaluation backlog ready |
| Stage 05_02 | Automation & evaluation tooling | LLM-as-judge automation, scoring dashboards, dataset exporters | Automation runs end-to-end, metrics visible, data catalogued |
| Stage 05_03 | Fine-tuning governance & rollout | Governance policy, runbooks, pilot fine-tune report | Governance approved, pilot results documented, next steps agreed |

## Success Criteria
- Benchmarks executed regularly with clear accuracy/coverage/coherence metrics.
- Dataset pipeline produces reproducible artefacts ready for fine-tuning.
- Governance ensures only validated datasets trigger fine-tuning, with rollback
  procedures in place.

## Stakeholders
- Tech Lead Agent: to be assigned when epic activated.
- ML/Research Agents: implement evaluation and fine-tuning automation.
- Operations/Compliance: review governance and monitoring plans.

## Risk & Mitigation Snapshot
- **Risk:** Evaluation metrics drift without oversight.  
  **Mitigation:** Schedule periodic benchmark reviews and calibrate scoring
  prompts.
- **Risk:** Fine-tuning introduces regressions.  
  **Mitigation:** Enforce approval workflow with rollback plan and guardrail
  tests before promotion.

## References
- `docs/specs/specs.md` – summarisation & fine-tuning requirements.
- `packages/multipass-reviewer` – source of review artefacts.
- `docs/PERFORMANCE_BENCHMARKS.md` – target location for benchmark outputs.

