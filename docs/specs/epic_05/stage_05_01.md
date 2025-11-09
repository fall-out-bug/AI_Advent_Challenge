# Stage 05_01 · Benchmark & Dataset Design

## Goal
Define evaluation methodology, dataset schemas, and sampling strategies for
summarisation outputs to support consistent benchmarking and fine-tuning prep.

## Checklist
- [ ] Review existing summarisation flows (digest pipeline, reviewer synthesis)
  to identify data sources.
- [ ] Define benchmark scenarios (e.g., channel digests, review summaries) and
  target metrics (coverage, accuracy, coherence, informativeness).
- [ ] Design dataset schema including metadata (language, source, timestamps,
  evaluator judgments).
- [ ] Establish sampling strategy (frequency, volume, language mix).
- [ ] Produce evaluation backlog with required automation tasks for Stage 05_02.

## Deliverables
- Benchmark plan document with scenarios, metrics, and acceptance thresholds.
- Dataset schema specification and initial sample dataset.
- Backlog of automation tasks with priorities and owners.

## Metrics & Evidence
- Sample dataset statistics (counts, language distribution).
- Draft benchmark scoreboard template (even if manual initially).
- Stakeholder approval notes (architecture, ML lead).

## Dependencies
- Reviewer artefacts and digest outputs available via shared storage.
- Coordination with EP01/EP03 for metrics/logging alignment.

## Exit Criteria
- Benchmark plan approved and published.
- Sample dataset validated and stored in agreed location.
- Automation tasks prioritised for Stage 05_02, no open blockers.

## Open Questions
- Do we include human-in-the-loop evaluations at this stage?
- What data retention policies apply to stored datasets?

