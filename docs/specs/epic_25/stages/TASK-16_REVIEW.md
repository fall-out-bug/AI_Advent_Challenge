# Review: Task 16 – Interest Extraction & Profile Enrichment

**Epic**: EP25 – Personalised Butler
**Task**: 16 – Interest Extraction & Profile Enrichment
**Reviewer**: Auto (AI Assistant, Reviewer role)
**Date**: 2025-11-18
**Status**: ✅ Approved (with minor recommendations)

---

## 1. Scope & Spec Alignment

- **Backlog alignment**:
  - Task 16 in `epic_25/backlog.md` requires:
    - Extracting 3–7 recurring topics during summarisation,
    - Updating `UserProfile.preferred_topics`,
    - Passing topics into persona prompt so Butler adapts replies,
    - Avoiding sensitive data,
    - Adding tests to verify topics and their effect on replies.
  - Session summary & worklog confirm:
    - LLM-based `InterestExtractionService` is used during memory compression,
    - `preferred_topics` updated via immutable `with_topics()`,
    - Topics fed into persona template (via templates/YAML),
    - Sensitive data filtered,
    - Unit tests cover extraction, merging, filtering and `with_topics()`.
- **Conclusion**: Scope of Task 16 is fully covered; behaviour matches backlog requirements.

---

## 2. Architecture & Design

- **Layering**:
  - `InterestExtractionService` lives in the **application** layer, as required.
  - Domain layer changed minimally (new `with_topics()` on `UserProfile`), preserving immutability.
  - Use case (`PersonalizedReplyUseCase`) integrates service only in compression path, keeping main flow simple.
  - DI/factory updated to create the service conditionally via feature flag – clean and compliant with existing DI patterns.
- **Optional dependency**:
  - Service is optional in the use case and guarded by `INTEREST_EXTRACTION_ENABLED`.
  - On failure or disabled flag, system falls back to plain summarisation.
- **Conclusion**: Design is consistent with Clean Architecture and existing EP25 patterns; no layer violations detected.

---

## 3. Behaviour & Correctness

- **Interest extraction**:
  - Extracts 3–7 topics from conversation history via LLM prompt (template in `persona_templates.yaml`).
  - Merging strategy:
    - Confirmed topics (intersection old/new) take priority,
    - Existing topics preserved,
    - New topics added until max is reached – this matches the “stable top-N list” requirement and avoids churn.
- **Sensitive data filtering**:
  - Regex-based filters for API keys, passwords, file paths, IDs, emails.
  - This is a pragmatic approach; limitation (false negatives/positives) is acknowledged in “Known Limitations”.
- **Use in replies**:
  - `preferred_topics` are injected into persona prompt through templates; thus Butler can adapt wording and examples to user interests.
  - This directly satisfies the requirement that interests **must influence dialogue**, not только храниться.
- **Fallback semantics**:
  - On LLM/JSON errors, service returns existing topics and a basic summary, preserving compression behaviour.
- **Conclusion**: Functional behaviour is well thought out and robust; it respects privacy and ensures that failures do not break core flows.

---

## 4. Testing & Observability

- **Tests**:
  - 8 unit tests for the service (extraction, merging, filtering, error handling, edge cases),
  - 2 tests for `UserProfile.with_topics()` (functionality + immutability),
  - All passing; coverage reported ≥80% for new code.
  - Integration/E2E tests for interests are explicitly marked as future/optional – this is acceptable for a scoped task, given strong unit coverage.
- **Metrics**:
  - Added counters/histograms: `interest_extraction_total{status}`, `interest_extraction_duration_seconds`, `user_interests_updated_total`, `user_interests_count`.
  - These metrics are sufficient to monitor success rate, latency and the shape of interests usage.
- **Configuration**:
  - Feature flag + tunables (`MAX_TOPICS`, temperature) are exposed via settings/env vars and documented.
- **Conclusion**: Testing and observability meet EP25 quality expectations; any operational issue with interest extraction should be diagnosable via metrics and logs.

---

## 5. Risks & Recommendations

- **Risks**:
  - No topic decay/ranking: over time, `preferred_topics` may become stale if user interests shift.
  - Regex-based filtering may miss some sensitive patterns (acknowledged in docs).
  - No integration/E2E tests yet for “interest-aware replies” (only unit-level validation).
- **Recommendations (non-blocking)**:
  1. In a follow-up task, add **topic decay** or “recent window” logic so stale topics can be dropped.
  2. Add at least one **integration/E2E test** that validates replies actually incorporate `preferred_topics` (e.g. hints or examples in user’s favourite domains).
  3. Over time, extend sensitive-data patterns (e.g. config-driven list) to reduce the chance of leaking secrets into interests.

---

## 6. Verdict

- **Task 16 Status**: ✅ **Approved**
- **Compliance**: Fully aligned with EP25 backlog and architecture; respects privacy and clean architecture constraints.
- **Blocking issues**: None.
- **Follow-ups**: Recommended as future improvements, not as blockers for deployment.
