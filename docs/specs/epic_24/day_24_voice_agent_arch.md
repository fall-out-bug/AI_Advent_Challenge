# Epic 24 · Day 24 Voice Agent Architecture Plan

## 1. Context & Goal
- Source: `docs/challenge_days.md#🔥-день-24-голосовой-агент-speech-→-llm-→-text`
- Objective: Enable Telegram voice messages → local/offline speech-to-text (STT) → user confirmation → Butler/LLM pipeline execution (e.g. channel digest request).
- Constraints:
  - Must follow Clean Architecture (domain interfaces, application use cases, infra adapters, presentation handlers).
  - STT must run offline (local model) and never send audio to external SaaS.
  - Russian language support first; latency not critical for MVP.
  - No permanent storage of raw audio/transcripts in Mongo (only transient processing).
  - Observability/metrics baseline inherited from EP23 (structured logs, `/metrics`, Loki traces).

## 2. Functional Requirements
1. Receive Telegram `voice` or `audio` updates (OGG/OPUS via Bot API).
2. Download file once, transcribe locally via STT adapter (Russian).
3. Present recognized text to user for confirmation (inline buttons).
4. On confirmation, route text to existing Butler/LLM flow (reuse `handle_user_message`).
5. Support at least digest command: “Сделай дайджест по каналу X за последние 24 часа”.
6. Handle rejection / re-record flow gracefully.

## 3. Non-Functional Requirements
- **Security:** Audio never leaves host; sanitized temp storage with automatic deletion.
- **Observability:** Metrics/logs per EP23:
  - `voice_transcriptions_total{status}` counters.
  - `voice_transcription_duration_seconds` histogram.
  - Structured logs include `trace_id`, `voice_request_id`.
- **Testing:** Unit tests for domain services, integration tests for Telegram handler + use case with mocked STT, characterization tests for Butler reuse.
- **Localization:** Prompts/confirmations in Russian.

## 4. Architecture Layers
### 4.1 Domain (`src/domain/`)
- **Interface `SpeechToTextService`**
  ```python
  class SpeechToTextService(Protocol):
      def transcribe(self, audio: bytes, language: str = "ru") -> TranscriptionResult: ...
  ```
- **Value Objects**
  - `TranscriptionResult`: `text`, `confidence`, `language`, `duration_ms`.
  - `VoiceCommand`: `id`, `user_id`, `transcription`, `state (pending|confirmed|rejected)`.

### 4.2 Application (`src/application/`)
- **Use Case `ProcessVoiceCommandUseCase`**
  - Dependencies: `SpeechToTextService`, `ButlerGateway` (wrapper over existing orchestrator), `ConfirmationGateway` (Telegram prompt sender).
  - Steps:
    1. Validate audio metadata (duration < 2 min).
    2. Call STT → get `TranscriptionResult`.
    3. Persist transient state (in-memory or Redis if available) via `VoiceCommandStore`.
    4. Trigger confirmation message with inline buttons (“Подтвердить”, “Повторить”).
- **Use Case `HandleVoiceConfirmationUseCase`**
  - On confirm: fetch stored transcription, call `ButlerGateway.handle_user_message`.
  - On reject: notify user to resend voice.

### 4.3 Infrastructure (`src/infrastructure/`)
- **STT Adapter** `OllamaSpeechToTextAdapter`
  - Wraps local Ollama HTTP API (`OLLAMA_HOST`, `OLLAMA_PORT`) with `whisper-small` RU model.
  - Sends PCM/WAV bytes to `/api/generate` (running on the same host) and parses transcription text + confidence.
  - Configured via settings: `stt_model_name`, `stt_min_confidence` (default 0.6), timeouts, retries.
  - Handles temp file creation from Telegram download with immediate cleanup via `try/finally`.
- **STT Adapter Fallback** `VoskSpeechToTextAdapter`
  - CPU-only fallback for environments without GPU/Ollama.
  - Shares the same `SpeechToTextService` interface; uses local Vosk RU model files.
- **VoiceCommandStore**
  - **Primary:** Shared Redis instance from Day 23 (`make day-23-up` stack).
  - **Fallback:** In-memory cache with TTL (for local dev / Redis outage).
  - Exposes `save(command: VoiceCommand)`, `get(command_id)`, `delete(command_id)`, enforces TTL (default 10 min).
- **Metrics**
  - Integrate with `src/infrastructure/metrics/*`.
  - Emit structured logs to Loki (include audio duration, confidence score).

### 4.4 Presentation (`src/presentation/telegram/`)
- **Handler `VoiceUpdateHandler`**
  - Subscribes to Telegram `voice` updates.
  - Downloads audio via existing Telegram API client, streams bytes to use case.
  - Sends confirmation message with inline keyboard referencing `command_id`.
- **Callback Handler**
  - Processes confirmation button clicks, calls `HandleVoiceConfirmationUseCase`.

## 5. Component Diagram (Textual)
```
Telegram Voice Update
   ↓ (Presentation)
VoiceUpdateHandler
   ↓ (Application)
ProcessVoiceCommandUseCase
   ↙                     ↘
SpeechToTextService   ConfirmationGateway (Telegram message)
   ↓                         ↓ user confirms
TranscriptionResult      Callback → HandleVoiceConfirmationUseCase
                               ↓
                         ButlerGateway.handle_user_message
                               ↓
                         Existing Butler/LLM pipeline
```

## 6. Data Flow
1. `VoiceUpdateHandler` downloads audio (OGG).
2. Use case converts to PCM/WAV temp file, passes bytes to `SpeechToTextService.transcribe`.
3. STT returns text; use case stores `VoiceCommand` (id with UUID, TTL=10 min). При ошибке STT или низкой уверенности команда **не** сохраняется, пользователю отправляется сообщение с просьбой перезаписать голос.
4. Use case sends message (RU):
   «Распознала: „…“. Подтвердить?» (кнопки «Подтвердить» / «Повторить»).
5. On confirm: `HandleVoiceConfirmationUseCase` pulls command, invokes Butler orchestrator (text route). Butler уже логирует и выполняет соответствующий сценарий (например, дайджест).
6. On reject: send prompt to resend audio, delete command state.

## 7. Interfaces & Contracts
### SpeechToTextService
```python
class SpeechToTextService(Protocol):
    def transcribe(self, audio: bytes, language: str = "ru") -> TranscriptionResult:
        """Offline transcription.

        Args:
            audio: Raw PCM/OGG bytes.
            language: ISO code ("ru" default).

        Returns:
            TranscriptionResult with text/confidence/duration.

        Raises:
            SpeechToTextError: on decoding failures.
        """
```

### ProcessVoiceCommandUseCase
```python
@dataclass
class ProcessVoiceCommandInput:
    command_id: UUID
    user_id: str
    audio_bytes: bytes
    duration_seconds: float
```
Constraints: reject if duration > 120s.

### Metrics
- `voice_transcriptions_total{status="success|error"}`.
- `voice_transcription_duration_seconds`.
- `voice_confirmation_pending` gauge (optional).

### ButlerGateway
```python
class ButlerGateway(Protocol):
    async def handle_user_message(self, user_id: str, text: str, session_id: str) -> str:
        """Delegate confirmed voice command text into existing Butler pipeline.

        Args:
            user_id: User identifier
            text: Confirmed transcription text
            session_id: Session identifier (generated as f"voice_{user_id}_{command_id}" or from Butler session manager)

        Returns:
            Response text from Butler orchestrator
        """
```

**Implementation:** Wraps `ButlerOrchestrator.handle_user_message()` in application layer adapter.

### ConfirmationGateway
```python
class ConfirmationGateway(Protocol):
    async def send_confirmation(self, user_id: str, text: str, command_id: UUID) -> None:
        """Send confirmation message to user with inline buttons.

        Args:
            user_id: Telegram user ID
            text: Recognized transcription text
            command_id: Voice command UUID for callback payload
        """
```

**Implementation:** Wraps Telegram bot API client in presentation layer.

## 8. Observability & Logging
- Structured logs at each step with `voice_command_id`, `user_id`, `transcription_length`.
- Trace timeline (download → stt → confirmation → butler).
- Loki alerts: high error rate >20% per minute.

## 9. Testing Strategy
1. **Unit**
   - `SpeechToTextService` mock verifying fallback paths.
   - `ProcessVoiceCommandUseCase` with mocked STT + confirmation gateway.
2. **Integration**
   - Telegram handler using fake update + stub STT returning deterministic text.
   - Confirmation callback hitting Butler mock ensures text forwarded.
3. **Characterization**
   - Butler digest flow already covered; add test voice scenario referencing new use case.

## 10. Backlog Links
- Add to `docs/specs/epic_24/backlog.md`:
  - TL24-07 Voice Agent: STT adapter, use cases, Telegram handlers, tests, docs.
- Update `docs/specs/progress.md` after implementation.

## 11. Decisions (TL-00 Confirmed)
1. **Storage for pending confirmations:** Shared Redis (Day 23 stack) primary; in-memory cache как fallback для dev/аварий.
2. **STT model selection:** Local Ollama + `whisper-small` RU (HTTP on localhost). Vosk RU модель как CPU-only fallback. Модели скачиваются локально при `ollama pull whisper-small`.
3. **STT confidence threshold:** < 0.6 triggers "low confidence" error (configurable via `stt_min_confidence` setting).
4. **Session ID strategy:** Generate per voice command as `f"voice_{user_id}_{command_id}"` or reuse Butler session manager if available.
5. **Butler command scope:** Allow any text (not just digest). After confirmation, pass transcription directly into Butler pipeline via `ButlerGateway`; unknown intents handled by existing NLP fallback.
6. **Error messages:** Hardcoded Russian strings for MVP (future: i18n system out of scope).

Implementation ready to start under Epic 24 TL-01 stage.
