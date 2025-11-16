# RU Localisation Spot-Check · Epic 23

Purpose: provide a reproducible checklist confirming that seeded benchmark samples preserve Russian-language fidelity and metadata before exporter verification (TL-01 DoD).

## Sampling Protocol
1. Generate channel counts via `benchmark_dataset_dir/snapshots/<date>/channel_counts.json`.
2. For each of the 5 RU channels, randomly select 5 documents (use `python scripts/quality/analysis/sample_ru_entries.py --channel <name> --count 5`).
3. Reviewers (one engineer, one bilingual Analyst) validate the following per sample:
   - `summary` contains RU headings + correct locale markers.
   - `raw_posts` include at least 3 RU sentences; no auto-translation artifacts.
   - `latency_ms` and `feature_flags` fields populated.
   - Timestamps fall within last 30 calendar days.
4. Record findings in the table below; all failures require remediation + re-run.

| Channel | Sample IDs | Summary RU? | Raw Posts RU? | Metadata Present? | Reviewer | Status |
| --- | --- | --- | --- | --- | --- | --- |
| channel_1 |  |  |  |  |  |  |
| channel_2 |  |  |  |  |  |  |
| channel_3 |  |  |  |  |  |  |
| channel_4 |  |  |  |  |  |  |
| channel_5 |  |  |  |  |  |  |

## Evidence Storage
- Completed checklist saved alongside channel snapshot: `benchmark_dataset_dir/snapshots/<date>/ru_spotcheck.md`.
- Link the saved checklist in TL-01 DoD evidence (plan Section 8).

## Sign-off
- Engineer Reviewer: …  
- Analyst Reviewer: …

