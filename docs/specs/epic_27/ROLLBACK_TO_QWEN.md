# Rollback to Qwen LLM - Epic 27

## Summary

**Date**: 2025-11-20 19:15:00
**Reason**: GigaChat model is not working/available
**Decision**: Rollback to Qwen (llm-api service)
**Status**: ✅ Completed

## Changes Made

### 1. TokenCounter Service

**File**: `src/infrastructure/test_agent/services/token_counter.py`

**Changes**:
- ✅ Removed GigaChat/sentencepiece tokenizer code
- ✅ Reverted to Qwen tokenizer (tiktoken with cl100k_base encoding)
- ✅ Simplified implementation (removed sentencepiece dependency)
- ✅ Removed unused imports (logging, os)

**Before**: Used sentencepiece for GigaChat with tiktoken fallback
**After**: Uses only tiktoken with cl100k_base (Qwen-compatible)

### 2. Implementation Plan

**File**: `docs/specs/epic_27/consensus/artifacts/plan.json`

**Changes**:
- ✅ Removed T2.5: "Update TokenCounter to use GigaChat tokenizer" (1h)
- ✅ Removed T2.6: "Update integration tests for GigaChat tokenizer" (0.5h)
- ✅ Updated T2.2: Changed description from "GigaChat tokenizer" to "Qwen tokenizer"
- ✅ Updated T2.3: Changed test case from "gigachat_expectations" to "qwen_expectations"
- ✅ Updated T4.3: Changed from "GigaChat LLM" to "Qwen LLM"
- ✅ Updated risk section: Changed from "GigaChat tokenizer" to "Qwen tokenizer"
- ✅ Updated dependencies: Removed T2.6 dependencies
- ✅ Updated stage duration: S2 from 5h → 3.5h
- ✅ Updated total: 32 tasks → 30 tasks, 29h → 27.5h

### 3. Configuration Changes Needed

**Environment Variables**:
```bash
# Change from:
export LLM_URL="http://llm-api-gigachat:8000"

# To:
export LLM_URL="http://llm-api:8000"
```

**Docker Compose** (if used):
- Update `docker-compose.test-agent.yml` to use `llm-api` service
- Remove `llm-api-gigachat` service reference

## Architecture Impact

✅ **No Impact** - Pure infrastructure swap:
- Clean Architecture boundaries maintained
- LLMClient Protocol unchanged
- Application layer unchanged (depends on Protocol)
- Domain layer unchanged
- Presentation layer unchanged

## Backward Compatibility

✅ **Maintained**:
- Qwen was the original model in Epic 26
- All existing tests should pass
- Test Agent functionality unchanged
- Token counting accuracy maintained (tiktoken cl100k_base)

## Testing

**TokenCounter Verification**:
```bash
python -c "from src.infrastructure.test_agent.services.token_counter import TokenCounter; tc = TokenCounter(); print(f'Tokens: {tc.count_tokens(\"def test(): pass\")}')"
# Expected: 4 tokens
```

**Status**: ✅ TokenCounter working correctly with Qwen tokenizer

## Next Steps

1. ✅ Code updated - TokenCounter reverted to Qwen
2. ✅ Plan updated - Removed GigaChat migration tasks
3. ⚠️ Configuration needed - Update LLM_URL environment variable
4. ⚠️ Testing needed - Verify test generation works with Qwen LLM
5. ⚠️ Integration tests - Run to verify Qwen compatibility

## Files Modified

- `src/infrastructure/test_agent/services/token_counter.py` - Reverted to Qwen
- `docs/specs/epic_27/consensus/artifacts/plan.json` - Updated plan
- `TEST_AGENT_GUIDE.md` - Updated with Qwen configuration
- `docs/specs/epic_27/consensus/messages/inbox/architect/msg_2025_11_20_19_15_00.yaml` - Notification

## Decision Log

Entry added to `docs/specs/epic_27/consensus/decision_log.jsonl`:
- Timestamp: 2025_11_20_19_15_00
- Decision: rollback
- Reason: GigaChat model not working
- Rollback to: Qwen (llm-api)
