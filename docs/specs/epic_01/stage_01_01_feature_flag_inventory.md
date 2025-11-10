# EP01 Stage 01_01 · Feature Flag Inventory & Decision Outline

## 1. Current Flag Readers

| Flag | Default | Readers | Notes |
|------|---------|---------|-------|
| `use_modular_reviewer` (`Settings.use_modular_reviewer`) | `True` | _No direct usage found_ | Defined in `src/infrastructure/config/settings.py`; not referenced elsewhere. |
| `USE_MODULAR_REVIEWER` (env export) | `1` (per docs) | Shell exports in docs/operations | Mirrors the same toggle; no runtime reads discovered. |
| `enable_log_analysis` | `True` | `src/application/use_cases/review_submission_use_case.py` (Pass 4 gating); multipass reviewer config builder | Controls log analysis pass. |
| `parser_strict_mode` | `False` | `src/domain/agents/mcp_aware_agent.py` | Enables strict JSON parsing. |
| `use_new_summarization` | `False` | `src/presentation/mcp/tools/channels/channel_digest.py`, `reminder_tools.py` | Phase 6 summarizer toggle. |
| `enable_quality_evaluation` | `True` | `src/application/use_cases/generate_channel_digest_by_name.py` | Adds quality evaluation scoring. |
| `enable_auto_finetuning` | `True` | `src/infrastructure/repositories/summarization_evaluation_repository.py`, `src/workers/finetuning_worker.py` | Controls automated fine-tuning job. |
| `enable_async_long_summarization` | `True` | `src/workers/summary_worker.py` | Async summarization worker path. |
| `bot_api_fallback_enabled` | `True` | `src/infrastructure/clients/telegram_utils.py` | Telegram channel discovery fallback. |
| `llm_fallback_enabled` | `False` | `src/infrastructure/clients/telegram_utils.py` | Extra LLM-based fallback. |
| `enable_llm_rerank` | `True` | `src/domain/services/channel_resolver.py` | Re-ranking candidate channels. |
| `hw_checker_mcp_enabled` | `True` | `src/workers/summary_worker.py` | Routes review results via MCP. |
| `external_api_enabled` | `False` | `summary_worker.py`, tests | External review publishing. |

## 2. Repository Search Summary

Command executed: `rg "use_modular_reviewer" src`  
Result: only definition found (no readers).

Command executed: `rg "USE_MODULAR_REVIEWER" -g'*'`  
Result: documentation references; no runtime consumption.

## 3. Decision Outline (Draft)

### Option A · Keep Flag Permanent
- **Pros:** Allows staged fallback to legacy reviewer if unexpected regressions surface.
- **Cons:** Encourages dual-path logic, increases testing matrix, and may mask issues (no current reader means toggle ineffective).

### Option B · Default-On + Deprecation Window (Recommended)
- **Plan:** Announce that modular reviewer is the canonical flow; keep flag for one Stage as a kill-switch; schedule removal (code + docs) once Stage 01_02 concludes.
- **Pros:** Simplifies architecture, ensures toggle is meaningful only during controlled window.
- **Cons:** Requires clear documentation and monitoring during deprecation.

### Option C · Remove Immediately
- **Pros:** Clean architecture, no dead toggles.
- **Cons:** No safety net during remediation; may concern stakeholders until confidence builds.

## 4. Next Steps

1. Present Options A–C to architecture/EP01 leads for decision.
2. If Option B accepted:
   - Draft decision log entry (location: `docs/specs/decisions/EP01_use_modular_reviewer.md`).
   - Update code to wire flag into DI for temporary kill-switch (if needed) or document removal timeline.
   - Schedule removal task in Stage 01_03 backlog.
3. If Option C chosen: add backlog ticket to remove flag immediately and update docs (EP01-S01-FLAG-001 extension).

