# Legacy Cluster E · Acceptance Matrix

| Task | Stage | Evidence | Owner | Status |
| --- | --- | --- | --- | --- |
| Approve lowercase normalization policy | TL-00 | Decision note + worklog entry | Tech Lead/Analyst | Pending |
| Inventory modules affected | TL-00 | Checklist attached to plan | Tech Lead | Pending |
| Implement TelegramClientAdapter + DI wiring | TL-01 | Adapter module diff, DI change | Dev D | Pending |
| Update existing callers to adapter | TL-01 | grep proof (no direct telegram_utils) | Dev D | Pending |
| Refactor ChannelNormalizer & helpers | TL-02 | Domain module diff + unit tests | Dev D | Pending |
| Update CLI/backoffice normalization usage | TL-02 | CLI diff, manual test log | Dev D | Pending |
| Refactor PostFetcherWorker to use adapter/DI | TL-03 | Worker code diff | Dev E | Pending |
| Update worker/unit/integration tests | TL-03 | Pytest log, coverage | QA | Pending |
| Update docs + Challenge Day references | TL-04 | Doc diffs (Days 11/17, new guide) | Tech Lead | Pending |
| Update work_log + gap table | TL-04 | Entries updated | Tech Lead | Pending |
