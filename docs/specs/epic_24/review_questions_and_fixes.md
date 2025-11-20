# Epic 24 · Review Questions & Fixes

**Reviewer:** cursor_reviewer_v1
**Date:** 2025-11-18
**Status:** ✅ **READY FOR IMPLEMENTATION** (все вопросы закрыты)

## Critical Issues (Resolved)

1. **STT Model Selection**
   - Решение: используем локальный Ollama (`/api/generate`) с моделью `whisper-small` RU; Vosk остаётся CPU fallback.
   - Обновлено в: `tech_lead_plan.md` (TL-00/TL-02), `day_24_voice_agent_arch.md`.

2. **Redis Availability**
   - Решение: shared Redis из Day 23 — основной storage; in-memory cache лишь fallback для dev/аварий.
   - Обновлено в TL-00/TL-02 и acceptance matrix.

3. **CI Metrics Gate**
   - Решение: вместо несуществующего `check_metrics.py` используем manual `curl …/metrics | grep voice_` (TL-05 tasks + CI gate таблица).

## High-Priority Clarifications (Resolved)

4. **ConfirmationGateway** — добавлен протокол (`src/domain/interfaces/confirmation_gateway.py`, TL-01).
5. **ButlerGateway** — добавлен протокол-адаптер (`src/domain/interfaces/butler_gateway.py`, TL-01).
6. **Temp File Cleanup** — TL-02 требует `try/finally` cleanup + optional TTL job.
7. **Session ID Strategy** — TL-03: `voice_{user_id}_{command_id}` или Butler session manager.
8. **Audio Conversion** — TL-03: OGG→WAV через `pydub.AudioSegment` (ffmpeg).
9. **Confidence Threshold** — TL-00: `stt_min_confidence = 0.6`.
10. **Error Messages** — TL-03: жёстко RU строки (“Команда отклонена…”, “Не удалось распознать голос…”).

## Summary Checklist
- [x] STT (Ollama + Vosk) финализирован.
- [x] Redis usage задокументирован.
- [x] Gateway протоколы определены.
- [x] Session ID, audio conversion, cleanup, RU UX и confidence threshold описаны.
- [x] CI gate заменён на manual metrics check.

Документы `tech_lead_plan.md`, `day_24_voice_agent_arch.md`, `acceptance_matrix.md` и связанные артефакты обновлены; можно передавать в разработку.
# Epic 24 · Review Questions & Fixes

**Reviewer:** cursor_reviewer_v1
**Date:** 2025-11-18
**Status:** ⚠️ **NEEDS CLARIFICATION** before implementation start

## 🔴 Critical Issues (Must Fix Before Start)

### 1. **STT Model Selection Inconsistency**
**Issue:** Plan mentions both "локальный Whisper small RU (GPU)" and "Ollama whisper", but these are different approaches:
- **Ollama** = HTTP API service (not truly offline/local binary)
- **Local Whisper** = Python binding or CLI binary (truly offline)

**Location:**
- `tech_lead_plan.md` TL-00: "STT stack: primary — локальный Whisper small RU (GPU)"
- `tech_lead_plan.md` TL-02: "mock Ollama API" in evidence
- `day_24_voice_agent_arch.md` §4.3: "Wraps local Whisper/Vosk binary via CLI or Python binding"

**Question:** Which approach is actually planned?
- Option A: Local Whisper Python binding (`whisper` package) — truly offline, no HTTP
- Option B: Ollama HTTP API (requires Ollama service running) — not truly offline
- Option C: Both (Whisper primary, Ollama as fallback) — but this contradicts "offline" requirement

**Recommendation:**
- Use **Option A** (local Whisper Python binding) for true offline support
- Remove Ollama references from TL-02 evidence
- Update TL-00 decision to explicitly state: "Local Whisper via `openai-whisper` Python package, no HTTP dependencies"

**Fix Required:**
```diff
- TL-02 evidence: "Adapter integration test using short sample audio fixture against mock Ollama API"
+ TL-02 evidence: "Adapter integration test using short sample audio fixture with local Whisper model file"
```

---

### 2. **Redis Availability Not Confirmed**
**Issue:** Plan assumes Redis from Day 23 shared infra, but `docs/operational/shared_infra.md` doesn't list Redis service.

**Location:**
- `tech_lead_plan.md` TL-00: "использовать существующий shared Redis из Day 23"
- `day_24_voice_agent_arch.md` §4.3: "use Redis or SharedStateStore (if not available, use in-memory cache with TTL)"

**Question:** Is Redis actually available in Day 23 shared infra?
- If YES: Add Redis to `shared_infra.md` service matrix
- If NO: Update plan to use in-memory cache as primary, Redis as optional enhancement

**Recommendation:**
- Check if Redis exists in `make day-23-up` or `docker-compose.yml`
- If missing: Update TL-00 decision to "in-memory cache with TTL (Redis optional for production scaling)"
- Update `VoiceCommandStore` implementation to prioritize in-memory, Redis as optional

**Fix Required:**
```diff
- TL-00: "использовать существующий shared Redis из Day 23"
+ TL-00: "Temporary storage: in-memory cache with TTL (default). Redis optional if available in shared infra."
```

---

### 3. **CI Metrics Check Script Missing**
**Issue:** Plan requires `scripts/ci/check_metrics.py --components voice_agent`, but this script doesn't exist.

**Location:**
- `tech_lead_plan.md` §6 CI/CD Gates: "Metrics check | `scripts/ci/check_metrics.py --components voice_agent`"

**Question:** Should we:
- Option A: Create the script (adds scope to TL-05)
- Option B: Use existing Prometheus scraping + manual verification
- Option C: Remove this gate and rely on integration tests

**Recommendation:**
- **Option B** (simpler): Remove this gate, add manual verification step in TL-05 DoD
- Or create minimal script: `scripts/ci/check_metrics.py` that greps `/metrics` endpoint for `voice_*` metrics

**Fix Required:**
```diff
- Metrics check | `scripts/ci/check_metrics.py --components voice_agent` | TL-02–TL-05 | All metrics registered | Yes |
+ Metrics check | Manual: `curl http://localhost:8000/metrics | grep voice_` | TL-05 | All metrics visible | Yes |
```

---

## 🟡 High Priority Issues (Clarify Before Implementation)

### 4. **ConfirmationGateway Not Defined**
**Issue:** Plan mentions `ConfirmationGateway` but doesn't specify if it's a new component or wrapper over existing Telegram API.

**Location:**
- `tech_lead_plan.md` TL-03: "trigger confirmation message via `ConfirmationGateway`"
- `day_24_voice_agent_arch.md` §4.2: "ConfirmationGateway (Telegram prompt sender)"

**Question:** What is `ConfirmationGateway`?
- New protocol/interface in domain layer?
- Wrapper over existing Telegram bot API client?
- Part of presentation layer?

**Recommendation:**
- Define as **Protocol in domain layer** (`src/domain/interfaces/confirmation_gateway.py`)
- Implementation in presentation layer wraps Telegram bot API
- Enables testability (mock in use case tests)

**Fix Required:** Add to TL-01:
```markdown
4. Define `ConfirmationGateway` protocol with method:
   `async def send_confirmation(user_id: str, text: str, command_id: UUID) -> None`
```

---

### 5. **ButlerGateway vs ButlerOrchestrator**
**Issue:** Plan mentions `ButlerGateway` but codebase has `ButlerOrchestrator.handle_user_message()`.

**Location:**
- `tech_lead_plan.md` TL-03: "call `ButlerGateway.handle_user_message`"
- `day_24_voice_agent_arch.md` §7: "ButlerGateway(Protocol)"

**Question:** Should we:
- Option A: Create `ButlerGateway` Protocol wrapping `ButlerOrchestrator` (adapter pattern)
- Option B: Use `ButlerOrchestrator` directly (simpler, but couples application to domain)

**Recommendation:**
- **Option A** (Clean Architecture): Create `ButlerGateway` Protocol in domain/interfaces
- Implementation in application layer wraps `ButlerOrchestrator`
- Enables testability and follows dependency inversion

**Fix Required:** Add to TL-01:
```markdown
5. Define `ButlerGateway` protocol wrapping ButlerOrchestrator:
   `async def handle_user_message(user_id: str, text: str, session_id: str) -> str`
```

---

### 6. **Temp File Cleanup Strategy Unclear**
**Issue:** Plan says "automatic cleanup" but doesn't specify when/how.

**Location:**
- `tech_lead_plan.md` TL-02: "automatic cleanup как при успешной транскрипции, так и при ошибках STT"

**Question:**
- Cleanup immediately after transcription?
- Cleanup on confirmation/rejection?
- Background job for orphaned files?

**Recommendation:**
- Cleanup **immediately after transcription** (success or error)
- Use `try/finally` block in adapter
- Add TTL-based cleanup job for safety (optional, TL-05)

**Fix Required:** Add to TL-02:
```markdown
6. Temp file cleanup: Use `try/finally` to delete temp file immediately after STT call (success or error).
   Optional: Background cleanup job for orphaned files (TTL=5 min) in TL-05.
```

---

### 7. **Session ID Source Not Specified**
**Issue:** `ButlerOrchestrator.handle_user_message()` requires `session_id`, but plan doesn't specify how to get it.

**Location:**
- `tech_lead_plan.md` TL-03: "call `ButlerGateway.handle_user_message`"
- Code: `ButlerOrchestrator.handle_user_message(user_id, message, session_id, force_mode)`

**Question:** How do we get `session_id` for voice commands?
- Generate new UUID per voice command?
- Reuse existing Telegram session?
- Use `user_id` as session_id?

**Recommendation:**
- Use **existing session management** from Butler (if available)
- Or generate session_id per voice command: `f"voice_{user_id}_{command_id}"`
- Document in TL-03 implementation

**Fix Required:** Add to TL-03:
```markdown
4. Session ID: Generate per voice command as `f"voice_{user_id}_{command_id}"` or reuse Butler session manager if available.
```

---

## 🟢 Medium Priority Issues (Nice to Have)

### 8. **Audio Format Conversion Details Missing**
**Issue:** Plan mentions "Convert Telegram OGG to PCM" but doesn't specify library/method.

**Location:**
- `tech_lead_plan.md` TL-03: "Convert Telegram OGG to PCM (utility)"

**Question:** Which library for OGG→PCM conversion?
- `pydub` (AudioSegment)?
- `ffmpeg` subprocess?
- Telegram Bot API already provides conversion?

**Recommendation:**
- Use `pydub` (already in dependencies or add to requirements)
- Or use Telegram Bot API `get_file()` which may provide WAV directly
- Document choice in TL-03

**Fix Required:** Add to TL-03:
```markdown
5. Audio conversion: Use `pydub.AudioSegment` for OGG→WAV conversion, or verify Telegram API provides WAV directly.
```

---

### 9. **Confidence Threshold Not Defined**
**Issue:** Plan mentions "low confidence" but doesn't specify threshold.

**Location:**
- `tech_lead_plan.md` TL-03: "On STT failure or low confidence: не сохранять команду"

**Question:** What is "low confidence" threshold?
- < 0.7?
- < 0.5?
- Configurable?

**Recommendation:**
- Default: 0.6 (configurable via Settings)
- Document in TL-00 decision

**Fix Required:** Add to TL-00:
```markdown
- STT confidence threshold: < 0.6 triggers "low confidence" error (configurable via `stt_min_confidence` setting)
```

---

### 10. **Error Messages Localization**
**Issue:** Plan says "Russian language support first" but error messages not specified.

**Location:**
- `tech_lead_plan.md` TL-03: "отправить пользователю понятное сообщение об ошибке"

**Question:** Should error messages be:
- Hardcoded Russian strings?
- Localized via i18n system?
- Configurable messages?

**Recommendation:**
- Hardcoded Russian strings for MVP (simpler)
- Document in TL-03 that messages are in Russian
- Future: i18n system (out of scope)

**Fix Required:** Add to TL-03:
```markdown
6. Error messages: Hardcoded Russian strings for MVP. Example: "Не удалось распознать голос. Попробуйте записать заново."
```

---

## 📋 Summary of Required Fixes

### Before TL-00 Sign-off:
1. ✅ Clarify STT model: Local Whisper Python binding (not Ollama HTTP)
2. ✅ Confirm Redis availability or switch to in-memory cache as primary
3. ✅ Define `ConfirmationGateway` and `ButlerGateway` protocols in TL-01
4. ✅ Specify session_id generation strategy
5. ✅ Define confidence threshold (default 0.6)

### Before TL-02 Start:
6. ✅ Remove Ollama references from TL-02 evidence
7. ✅ Specify audio conversion library (pydub or Telegram API)
8. ✅ Document temp file cleanup strategy (immediate + optional background job)

### Before TL-05:
9. ✅ Replace `check_metrics.py` gate with manual verification or create minimal script
10. ✅ Document error message localization approach (hardcoded Russian for MVP)

---

## ✅ Strengths of Current Plan

1. ✅ **Clean Architecture alignment** — Proper layer separation (domain → application → infrastructure → presentation)
2. ✅ **Offline-first approach** — Correctly prioritizes local STT over SaaS
3. ✅ **Observability integration** — Reuses EP23 metrics/logging patterns
4. ✅ **Testing strategy** — Good coverage (unit, integration, characterization)
5. ✅ **Risk awareness** — Identifies key risks (accuracy, disk, Redis, Butler intent)

---

## 🎯 Recommended Next Steps

1. **TL-00 Enhancement:** Add explicit decisions on:
   - STT model: Local Whisper Python binding (`openai-whisper` package)
   - Storage: In-memory cache primary, Redis optional
   - Confidence threshold: 0.6 (configurable)
   - Session ID: Generate per command `f"voice_{user_id}_{command_id}"`

2. **TL-01 Enhancement:** Add protocol definitions:
   - `ConfirmationGateway` protocol
   - `ButlerGateway` protocol (wrapping ButlerOrchestrator)

3. **TL-02 Fix:** Remove Ollama references, specify Whisper Python binding

4. **TL-03 Enhancement:** Add details on:
   - Audio conversion (pydub or Telegram API)
   - Session ID generation
   - Error message localization

5. **TL-05 Fix:** Replace metrics check gate with manual verification

---

**Overall Assessment:** Plan is **well-structured** but needs **clarifications on STT model, Redis availability, and gateway protocols** before implementation can start safely.

**Confidence Level:** Medium (will be High after clarifications)
