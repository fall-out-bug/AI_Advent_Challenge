# Legacy Cluster D · Acceptance Matrix

| Task | Stage | Evidence | Owner | Status |
| --- | --- | --- | --- | --- |
| Approve LLM client interface + settings structure | TL-00 | Design doc / worklog entry | Tech Lead/Architect | Pending |
| Implement `LLMClientProtocol` + config | TL-01 | Code diff, mypy report | Dev C | Pending |
| Refactor existing clients to use protocol & settings | TL-01 | Client module diffs, tests | Dev C | Pending |
| Introduce dataclass for map-reduce chunk params | TL-02 | Summarizer module diff | Dev C | Pending |
| Update MapReduceSummarizer to use protocol + dataclass | TL-02 | Code diff, docstrings | Dev C/B | Pending |
| Update unit tests for LLM clients | TL-03 | `pytest tests/llm/test_llm_client.py` log | QA | Pending |
| Update summarizer tests & add regression cases | TL-03 | `pytest tests/unit/infrastructure/llm/summarizers` log | QA | Pending |
| Document LLM config & challenge day references | TL-04 | Doc diffs (`config_llm_clients.md`, `docs/challenge_days.md`) | Tech Lead | Pending |
| Update work_log & gap closure table | TL-04 | Entries + table status | Tech Lead | Pending |

