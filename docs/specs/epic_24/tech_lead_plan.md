# Epic 24 · Tech Lead Implementation Plan
_Day 24 · Voice Agent (Speech → LLM → Text)_

## 1. Metadata & Inputs
| Field | Value |
| --- | --- |
| Epic | EP24 |
| Scope | Voice-to-text flow for Telegram bot with confirmation and Butler integration |
| Tech Lead | cursor_tech_lead_v1 |
| Date | 2025-11-18 |
| Source Requirements | `docs/challenge_days.md#🔥-день-24-голосовой-агент-speech-→-llm-→-text` |
| Architecture Reference | `docs/specs/epic_24/day_24_voice_agent_arch.md` |
| Dependencies | EP23 observability stack, Butler orchestrator, shared infra (Mongo/Redis/LLM) |

## 2. Objectives & Assumptions
- Offline STT: audio never leaves host; adapters wrap local Whisper/Vosk.
- Russian language support first; other languages optional.
- Audio/transcripts stored transiently (cache/Redis) only for pending confirmation.
- Observability baseline from EP23: structured logs, Prometheus metrics, Loki traces.
- Telegram bot already handles text commands; we reuse Butler pipeline for post-confirmation execution.

## 3. Stage Overview
| Stage | Objective | Owner(s) | Duration (d) | Dependencies | Evidence |
| --- | --- | --- | --- | --- | --- |
| TL-00 | Scope confirmation & decisions | Tech Lead + Architect + Analyst | 1 | — | Decisions log, updated backlog |
| TL-01 | Domain contracts & value objects | Dev A | 1.5 | TL-00 | New interfaces, unit tests |
| TL-02 | Infrastructure STT adapter & storage | Dev B | 2 | TL-01 | Adapter code, integration stub, metrics |
| TL-03 | Application use cases & gateways | Dev A + Dev B | 2 | TL-02 | Use case code, service wiring |
| TL-04 | Presentation layer integration (Telegram + Butler) | Dev C | 2 | TL-03 | Handler code, callback wiring |
| TL-05 | Testing, observability, docs & rollout | QA + Tech Lead | 1.5 | TL-04 | Test logs, metrics snapshots, doc diffs |

Parallelisation note: TL-01 and TL-02 can overlap partially (adapter scaffold mocked), but final wiring waits for TL-01 sign-off.

## 4. Stage Details
### TL-00 · Scope Confirmation
- Decisions:
  - **STT stack:** primary — локальный Ollama (`/api/generate`) с моделью `whisper-small` RU (на том же хосте, без внешних SaaS); fallback — Vosk CPU adapter для сред без GPU.
  - **Temporary storage type:** shared Redis из Day 23 (тот же сервис `make day-23-up`, обязательный для прод), in-memory cache используется только для локальной разработки/аварий.
  - **Confirmation window length:** default 10 min (TTL для pending commands).
  - **STT confidence threshold:** < 0.6 triggers "low confidence" error (configurable via `stt_min_confidence` setting).
  - **Session ID strategy:** генерировать per voice command как `f"voice_{user_id}_{command_id}"` (или использовать существующий Butler session manager если доступен).
  - **Butler intent coverage:** любой подтверждённый текст маршрутизируется в текущий Butler pipeline (не только дайджест); неизвестные intents обрабатываются стандартным NLP fallback.
- Deliverables:
  - `docs/specs/epic_24/backlog.md` updated with TL24-07 tasks.
  - Worklog entry capturing decisions.

### TL-01 · Domain Contracts
- Tasks:
  1. Create `SpeechToTextService` protocol + `TranscriptionResult`, `VoiceCommand` value objects in `src/domain/voice/`.
  2. Define errors (`SpeechToTextError`, `InvalidVoiceCommandError`).
  3. Define `ConfirmationGateway` protocol (`src/domain/interfaces/confirmation_gateway.py`) with method:
     `async def send_confirmation(user_id: str, text: str, command_id: UUID) -> None`
  4. Define `ButlerGateway` protocol (`src/domain/interfaces/butler_gateway.py`) wrapping ButlerOrchestrator:
     `async def handle_user_message(user_id: str, text: str, session_id: str) -> str`
  5. Provide factory/dataclass for use case inputs (`ProcessVoiceCommandInput`, `HandleVoiceConfirmationInput`).
- Evidence:
  - Type-hinted modules with docstrings.
  - Unit tests for value objects (validation, state transitions).
  - API documented in `docs/specs/epic_24/day_24_voice_agent_arch.md` appendix (auto-link).

### TL-02 · Infrastructure STT Adapter & Storage
- Tasks:
  1. Implement `OllamaSpeechToTextAdapter` targeting локальный Ollama API (`OLLAMA_HOST`, `OLLAMA_PORT`, `STT_MODEL=whisper-small`), принимающий PCM/WAV bytes → текст (HTTP внутри локального хоста).
  2. Provide fallback `VoskSpeechToTextAdapter` (CPU) sharing the same interface для сред без доступного GPU.
  3. Add `VoiceCommandStore` (Redis implementation primary, reusing Day 23 shared Redis; предусмотреть in-memory fallback только для дев-режима/аварий). Methods: `save`, `get`, `delete`, TTL handling.
  4. Add metrics: `voice_transcriptions_total{status="success|error"}`, `voice_transcription_duration_seconds` histogram.
  5. Ensure temp audio files stored in `/tmp/voice_agent/<uuid>.wav` with **immediate cleanup** (use `try/finally` block) как при успешной транскрипции, так и при ошибках STT. Optional: background cleanup job для orphaned files (TTL=5 min) в TL-05.
- Evidence:
  - Adapter integration test using short sample audio fixture with mock Ollama API (плюс опциональный реальный тест при наличии модели) и отдельный тест для Vosk fallback.
  - Store unit tests с Redis (fakeredis) + in-memory fallback.
  - Metrics visible via `/metrics` endpoint.

### TL-03 · Application Use Cases
- Tasks:
  1. Implement `ProcessVoiceCommandUseCase`:
     - Validate audio metadata (duration < 120s).
     - Convert Telegram OGG to WAV using `pydub.AudioSegment` (ffmpeg backend).
     - Call STT service, check confidence threshold (default 0.6), store command only if confidence ≥ threshold.
     - Trigger confirmation message via `ConfirmationGateway` (Russian hardcoded messages for MVP).
  2. Implement `HandleVoiceConfirmationUseCase`:
     - On confirm: retrieve command, generate session_id `f"voice_{user_id}_{command_id}"` (или реиспользовать Butler session manager), call `ButlerGateway.handle_user_message`.
     - On reject: delete command and prompt user to resend (RU message: «Команда отклонена. Запишите голос заново.»).
     - On STT failure/low confidence: не сохранять команду, отправить RU сообщение об ошибке («Не удалось распознать голос. Попробуйте записать заново.») и предложить перезаписать.
  3. Add instrumentation (structured logs w/ `voice_command_id`, `user_id`, `transcription_length`, `confidence_score`).
- Evidence:
  - Use case unit tests (success, reject, STT error, low confidence, timeout).
  - Mock-based tests verifying `ConfirmationGateway` / `ButlerGateway` interactions.

### TL-04 · Presentation Integration
- Tasks:
  1. Extend Telegram bot: `VoiceUpdateHandler` downloads audio, invokes `ProcessVoiceCommandUseCase`.
  2. Add callback handler for confirmation buttons (with `command_id` payload).
  3. Ensure existing Butler pipeline handles forwarded text seamlessly (maybe via new intent tag `voice_confirmed` for logging).
  4. Add CLI/Make target to simulate voice event for local testing.
- Evidence:
  - Manual test walkthrough documented (voice message -> confirmation -> digest).
  - Telegram integration test (mock Bot API) verifying handler flow.

### TL-05 · Testing, Observability & Docs
- Tasks:
  1. Expand integration tests: end-to-end simulation with fake Telegram payload + stub STT, verifying Butler invocation.
  2. Add Loki alert rules for STT error spikes (reuse EP23 format).
  3. Document user instructions in `docs/challenge_days.md` Day 24 section (already seeded) with final commands + video link.
  4. Update `docs/specs/epic_24/acceptance_matrix.md`, `work_log.md`, and `dev_handoff.md`.
  5. Manual metrics verification: `curl http://localhost:<port>/metrics | grep voice_` recorded in work log (replaces non-existent CI script).
- Evidence:
  - CI log with relevant `pytest` suites.
  - `/metrics` curl output (voice_* counters) attached to work log + Loki alert diff.
  - Doc diffs committed.

## 5. Testing Strategy
| Level | Suites / Files | Notes |
| --- | --- | --- |
| Unit | `tests/unit/domain/voice/test_value_objects.py`, `tests/unit/infrastructure/stt/test_ollama_adapter.py`, `tests/unit/infrastructure/stt/test_vosk_adapter.py`, `tests/unit/application/voice/test_process_voice_command.py` | Use fixtures for audio bytes, mocking STT results. |
| Integration | `tests/integration/presentation/telegram/test_voice_handler.py`, `tests/integration/application/voice/test_voice_confirmation_flow.py` | Use fake Telegram updates & fakeredis. |
| Observability | `tests/integration/metrics/test_voice_metrics.py` | Ensures metrics registered and counters increment. |

## 6. CI/CD Gates
| Gate | Command | Applies To | Threshold | Blocking |
| --- | --- | --- | --- | --- |
| Lint | `make lint` | All stages | 0 errors | Yes |
| Typecheck | `mypy src/ --strict` | TL-01–TL-04 | 100% coverage | Yes |
| Unit tests | `pytest tests/unit/voice tests/unit/application/voice tests/unit/infrastructure/stt` | TL-01–TL-03 | Pass | Yes |
| Integration tests | `pytest tests/integration/presentation/telegram tests/integration/application/voice` | TL-04–TL-05 | Pass | Yes |
| Coverage | `pytest --cov=src --cov-report=xml` | TL-03–TL-05 | ≥80% overall | Yes |
| Metrics check | Manual: `curl http://localhost:8000/metrics | grep voice_` | TL-05 | All metrics visible | Yes |

## 7. Traceability
| Requirement | Stage | Evidence |
| --- | --- | --- |
| Offline STT transcription | TL-02 | Adapter tests + metrics |
| Confirmation flow | TL-03 + TL-04 | Use case tests + Telegram handler logs |
| Butler integration | TL-03 + TL-04 | Integration test showing digest command execution |
| Observability | TL-02 + TL-05 | Metrics snapshots + Loki alert config |
| Documentation | TL-05 | `docs/challenge_days.md`, dev handoff, work log |

## 8. Risk Register
| Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- |
| STT accuracy insufficient | Medium | Medium | Allow fallback engine, expose confidence to user for manual confirmation. |
| Large audio files consume disk | Medium | Low | Enforce duration limit + cleanup temp files immediately. |
| Redis unavailable | Low | Medium | Provide in-memory fallback with warning; queue revisit for prod. |
| Butler intent mismatch | Medium | Low | Log unrecognised commands, route to NLP fallback. |
| Telegram API rate limits | Low | Low | Reuse existing throttling/backoff logic. |

## 9. Handoff Checklist
- [ ] TL-00 decisions logged (STT model, storage, intent scope).
- [ ] Domain interfaces merged with docstrings/tests.
- [ ] STT adapter + store implemented with metrics.
- [ ] Use cases & gateways implemented with structured logging.
- [ ] Telegram handlers wired with manual and automated tests.
- [ ] Metrics + Loki alerts updated; docs & acceptance matrix signed.
