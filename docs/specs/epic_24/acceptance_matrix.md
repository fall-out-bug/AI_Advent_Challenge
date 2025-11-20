# Epic 24 · Acceptance Matrix (Day 24 Voice Agent)

| Task | Stage | Evidence | Owner | Status |
| --- | --- | --- | --- | --- |
| TL-00: Confirm STT model (Ollama `whisper-small` + Vosk fallback), shared Redis usage, confidence threshold (0.6), session_id strategy, ButlerGateway/ConfirmationGateway protocols | TL-00 | Decision log in `work_log.md`, backlog update | Tech Lead | Pending |
| TL-01: Define `SpeechToTextService`, value objects, domain errors, `ConfirmationGateway`, `ButlerGateway` protocols | TL-01 | `src/domain/voice/*`, `src/domain/interfaces/confirmation_gateway.py`, `src/domain/interfaces/butler_gateway.py` diff, unit tests | Dev A | Pending |
| TL-02: Implement STT adapters (Ollama API + Vosk fallback) + temp file handling | TL-02 | Adapter code + integration test (mock Ollama + optional real) + metrics | Dev B | Pending |
| TL-02: Implement `VoiceCommandStore` (Redis primary + in-memory fallback) | TL-02 | Store module, fakeredis tests + in-memory fallback tests | Dev B | Pending |
| TL-03: Implement `ProcessVoiceCommandUseCase` + logging (audio conversion, confidence check, session_id generation) | TL-03 | Use-case code, unit tests, pydub integration | Dev A | Pending |
| TL-03: Implement `HandleVoiceConfirmationUseCase` (confirm/reject + STT error UX, Russian error messages) | TL-03 | Use-case code, unit tests (ok, reject, STT failure, low confidence), ButlerGateway integration | Dev A | Pending |
| TL-04: Add Telegram voice handler + confirmation callbacks | TL-04 | Handler diff, integration test log | Dev C | Pending |
| TL-04: Wire Butler gateway & manual walkthrough | TL-04 | Manual test doc / video link | Dev C | Pending |
| TL-05: Add metrics, Loki alerts, docs updates | TL-05 | `/metrics` snapshot, alert diff, doc updates | Tech Lead | Pending |
| TL-05: Update `dev_handoff.md`, `work_log.md`, `challenge_days.md` | TL-05 | Doc diffs + worklog entries | Tech Lead | Pending |

Status legend: Pending / In Progress / Done / Blocked.
