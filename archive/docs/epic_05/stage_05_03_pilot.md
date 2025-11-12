# Stage 05_03 Pilot Plan · Fine-Tuning RU Summarisation

## Objective
Run a single fine-tuning cycle on the RU channel digest model to validate
Stage 05 governance, using datasets produced in Stage 05_02.

## Inputs
- Dataset: `data/benchmarks/benchmark_digest_ru_v1/2025-11-09_samples.jsonl`
- Model baseline: `qwen-7b` (summarisation stack, pre-finetune)
- Training target: `qwen-7b-ft-ru-digest-stage05`
- Prompt version: `benchmark-2025-11-v1`

## Baseline Metrics (Dry-Run Benchmark)
| Metric            | Value | Threshold | Status |
|-------------------|-------|-----------|--------|
| Coverage          | 0.89  | ≥0.88 pass / ≥0.80 warn | Warn |
| Accuracy          | 0.89  | ≥0.90 pass / ≥0.85 warn | Warn |
| Coherence         | 0.89  | ≥0.90 pass / ≥0.85 warn | Warn |
| Informativeness   | 0.91  | ≥0.88 pass / ≥0.82 warn | Pass |
| Latency (P95)     | 189.05s | ≤210s pass / ≤240s warn | Pass |

## Fine-Tuning Configuration
- Epochs: 1 (pilot)
- Batch size: 4
- Learning rate: 2e-5
- Optimiser: AdamW
- Seed: 42
- Max input tokens: 1024
- Output repository: `models/qwen-7b-ft-ru-digest-stage05`

## Evaluation Plan
1. Post-training benchmark using Stage 05 pipeline (live run when data available).
2. Additional evaluation: manual inspection of 5 samples for coverage of key facts.
3. Compare metrics vs baseline; acceptance requires improving coverage/accuracy
   above 0.90 without degrading latency.

## Rollback
- Keep baseline model artefact `qwen-7b` in registry.
- If new model fails acceptance, revert deployment pointer and clean up ft model.

## Release Coordination
- Schedule release alongside main product minor release; no separate cadence.
- Notify operations after evaluation with go/no-go decision.

## Outstanding
- Await live dataset expansion (Epic 23) for full evaluation run.
