# Epic 21 RAG++ · Operations Runbook

**Version**: 1.0
**Last Updated**: 2025-11-12
**Owner**: Tech Lead
**Audience**: DevOps, SRE, On-call Engineers

---

## 🎯 Overview

This runbook covers operations for the RAG++ (Reranking & Relevance Filtering) feature in Epic 21.

**Key Components**:
- Threshold filtering (fast, deterministic)
- LLM-based reranking (Qwen2.5-7B-Instruct, temperature=0.5)
- Feature flag: `enable_rag_plus_plus`
- Prometheus metrics for observability

---

## 🚀 Feature Flag Management

### Feature Flag: `enable_rag_plus_plus`

**Type**: Single-toggle (all-or-nothing, no canary rollout)

**Location**:
- Config file: `config/retrieval_rerank_config.yaml`
- Environment variable: `RAG_PLUS_PLUS_ENABLED` (overrides config)

**Default**: `false` (disabled, opt-in)

### Enable RAG++

**When**: After Stage 21_04 validation shows ≥60% win rate and <5s latency

**Procedure**:
1. Update config:
   ```yaml
   feature_flags:
     enable_rag_plus_plus: true
   ```
2. Deploy config change (hot-reload or restart service)
3. Verify via metrics: `rag_rerank_duration_seconds` counter increases
4. Monitor latency: `rag_retrieval_latency_seconds{mode="rag_plus_plus"}`

**Verification**:
```bash
# Check feature flag status via API
curl -s http://localhost:8000/health | jq '.features.rag_plus_plus'

# Expected: {"enabled": true, "strategy": "llm"}
```

### Disable RAG++ (Rollback)

**When**: Win rate <50% OR latency >8s OR fallback rate >10%

**Procedure**:
1. Set flag to `false` in config
2. Redeploy (or hot-reload if supported)
3. Verify RAG mode (no reranking) via logs
4. Create incident report

**SLA**: <5 minutes

---

## 📊 Monitoring & Dashboards

### Prometheus Metrics

**Location**: `/metrics` endpoint

**Key Metrics**:

| Metric | Type | Description | Alert Threshold |
|--------|------|-------------|-----------------|
| `rag_rerank_duration_seconds` | Histogram | Rerank latency (per query) | p95 >5s |
| `rag_chunks_filtered_total` | Counter | Chunks filtered by threshold | - |
| `rag_rerank_score_variance` | Histogram | Score variance (repeated runs) | >0.2 std dev |
| `rag_reranker_fallback_total` | Counter | Fallback events (timeout/error) | Rate >10% |
| `rag_retrieval_latency_seconds{mode="rag_plus_plus"}` | Histogram | End-to-end retrieval latency | p95 >8s |

### Grafana Dashboard

**Dashboard**: `RAG++ Performance & Reliability`

**Panels**:
1. **Rerank Latency** (p50, p95, p99) — target p95 <3s
2. **Fallback Rate** (%) — target <5%
3. **Score Variance** (stddev) — acceptable <0.15
4. **Chunks Filtered** (rate) — informational
5. **Win Rate** (manual annotation) — target ≥60%

**Access**: http://grafana.internal/d/rag-plus-plus

---

## 🔧 Configuration

### Config File Structure

**File**: `config/retrieval_rerank_config.yaml`

```yaml
retrieval:
  top_k: 5
  score_threshold: 0.30
  vector_search_headroom_multiplier: 2

reranker:
  enabled: false  # Controlled by feature flag
  strategy: "off"  # "off" | "llm" | "cross_encoder"
  llm:
    model: "qwen2.5-7b-instruct"
    temperature: 0.5
    seed: null  # Set for reproducibility
    temperature_override_env: "RAG_RERANK_TEMPERATURE"
    max_tokens: 256
    timeout_seconds: 3

feature_flags:
  enable_rag_plus_plus: false
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RAG_PLUS_PLUS_ENABLED` | `false` | Enable RAG++ (overrides config) |
| `RAG_SCORE_THRESHOLD` | `0.30` | Similarity threshold for filtering |
| `RAG_TOP_K` | `5` | Retrieval top_k override |
| `RAG_RERANKER_ENABLED` | `false` | Enable reranker (independent of flag) |
| `RAG_RERANKER_STRATEGY` | `off` | Reranker strategy |
| `RAG_RERANK_TEMPERATURE` | `0.5` | LLM temperature (override for debugging) |
| `RAG_RERANK_TIMEOUT` | `3` | Reranker timeout (seconds) |

### Tuning Parameters

**Threshold** (`score_threshold`):
- **0.3**: Conservative (more recall, less precision)
- **0.35**: Balanced (recommended default)
- **0.4**: Aggressive (more precision, less recall)

**Temperature**:
- **0.2**: Deterministic (less variance, less nuanced)
- **0.5**: Balanced (default, acceptable variance)
- **0.8**: Creative (high variance, NOT recommended for ranking)

### CLI Usage

`rag:compare` and `rag:batch` support runtime toggles for filtering and reranking:

```bash
# Enable filtering with conservative threshold (recommended)
poetry run cli rag:compare \
  --question "Что такое MapReduce?" \
  --filter \
  --threshold 0.30

# Enable LLM reranker (requires feature flag enabled)
poetry run cli rag:compare \
  --question "Расскажи про стадии shuffle" \
  --filter \
  --reranker llm

# Batch mode with overrides
poetry run cli rag:batch \
  --queries docs/specs/epic_20/queries.jsonl \
  --out results_ep21.jsonl \
  --filter \
  --threshold 0.30 \
  --reranker llm
```

Flags override config and environment variables with highest precedence.

### Demo Script (`day_21_demo.py`)

Для записи сравнительного скринкаста предусмотрен отдельный сценарий:

```bash
# Настроить окружение перед запуском
export LLM_URL="http://127.0.0.1:11434"
export LLM_MODEL="mistral:7b-instruct"
export EMBEDDING_API_URL="http://127.0.0.1:11434"
export MONGODB_URL="mongodb://admin:secure_mongo_password_456@127.0.0.1:27017/butler?authSource=admin"

# Убедитесь, что Ollama запущен и модели подтянуты:
# curl -X POST http://127.0.0.1:11434/api/pull -d '{"name":"mistral:7b-instruct"}'
# curl -X POST http://127.0.0.1:11434/api/pull -d '{"name":"nomic-embed-text"}'

# Терминал 1: Базовый бот
make day_21_demo args="--persona 1 --filter --threshold 0.25 --reranker off"

# Терминал 2: Ехидный дедушка с LLM-реранкером
make day_21_demo args="--persona 2 --filter --threshold 0.25 --reranker llm"
```

Скрипт содержит 10 дефолтных вопросов (покрывают Clean Architecture, workflow отчётов, CLI, фильтрацию, метрики и rollback). При необходимости можно задать свой список: параметр `--questions` принимает путь к текстовому файлу (UTF‑8, один вопрос на строку). Скрипт автоматически выводит ответы в двух режимах (без RAG и с RAG++) и список использованных чанков — их достаточно запустить в двух терминалах параллельно для итогового скринкаста.

---

## 🐛 Troubleshooting

### Issue: High Fallback Rate (>10%)

**Symptoms**:
- `rag_reranker_fallback_total` counter increasing rapidly
- Logs show `rag_rerank_failed` events

**Possible Causes**:
1. LLM service timeout (>3s)
2. LLM service unavailable (503 errors)
3. Malformed LLM responses (JSON parse errors)

**Diagnosis**:
```bash
# Check reranker error logs
kubectl logs -l app=rag-service | grep rag_rerank_failed | tail -20

# Check LLM service health
curl -s http://llm-service:8000/health | jq .
```

**Resolution**:
1. If LLM timeout: Increase `timeout_seconds` to 5s (temporary)
2. If LLM unavailable: Restart LLM service, verify Qwen model loaded
3. If parse errors: Check LLM prompt template, ensure JSON-only output
4. If persistent: Disable RAG++ (rollback), file incident

---

### Issue: High Latency (p95 >5s)

**Symptoms**:
- `rag_rerank_duration_seconds{quantile="0.95"}` >5s
- User complaints about slow responses

**Possible Causes**:
1. LLM model overloaded (high concurrent requests)
2. Large chunk count (>5 chunks per query)
3. Network latency to LLM service

**Diagnosis**:
```bash
# Check rerank latency distribution
curl -s http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rag_rerank_duration_seconds_bucket)

# Check LLM service load
kubectl top pod -l app=llm-service
```

**Resolution**:
1. Reduce `top_k` to 3 (fewer chunks to rerank)
2. Increase `score_threshold` to 0.4 (more aggressive filtering)
3. Scale LLM service replicas (horizontal scaling)
4. Consider cross-encoder (faster, 300-500ms) if LLM too slow

---

### Issue: Low Win Rate (<50%)

**Symptoms**:
- Manual evaluation shows RAG++ worse than RAG
- User feedback negative

**Possible Causes**:
1. Threshold too high (relevant chunks filtered out)
2. LLM reranker scoring poorly (prompt issues)
3. Query set not suited for reranking

**Diagnosis**:
```bash
# Review Stage 21_04 report
cat docs/specs/epic_21/stage_21_04_report.md

# Check examples of degraded queries
grep "rag_comparison_completed" logs/rag.log | grep "win_rate: false"
```

**Resolution**:
1. Lower threshold to 0.3 (more recall)
2. Review and refine reranker prompt template
3. Run ablation study (Stage 21_04) on specific query categories
4. If unfixable: Disable RAG++, defer to Epic 22

---

### Issue: High Score Variance (>0.2 stddev)

**Symptoms**:
- `rag_rerank_score_variance` >0.2 for same query across runs
- Non-deterministic outputs confusing users

**Possible Causes**:
1. Temperature too high (0.5 → more variance)
2. Query ambiguous (LLM uncertain)

**Diagnosis**:
```bash
# Run same query 5 times, measure variance
python scripts/rag/measure_variance.py --query-id arch_001 --runs 5

# Check temperature setting
grep temperature config/retrieval_rerank_config.yaml
```

**Resolution**:
1. Lower temperature to 0.3 (more deterministic, less nuanced)
2. Set `seed: 42` for reproducibility (experiments only)
3. Improve prompt clarity (add examples, tie-breakers)
4. If acceptable: Document variance as expected behavior (<0.15 stddev OK)

---

## 🔥 Rollback Procedure

### Trigger Conditions

**Immediate Rollback** if ANY:
- RAG++ win rate <50% (Stage 21_04 validation)
- p95 latency >8s for dialog queries
- Fallback rate >10% (unreliable reranker)
- Critical production incident (data loss, crashes)

### Rollback Steps

**SLA**: <5 minutes

1. **Disable Feature Flag**
   ```bash
   # Edit config
   vim config/retrieval_rerank_config.yaml
   # Set: enable_rag_plus_plus: false
   ```

2. **Deploy Config Change**
   ```bash
   # Option A: Hot-reload (if supported)
   kubectl exec rag-service -- kill -HUP 1

   # Option B: Rolling restart
   kubectl rollout restart deployment/rag-service
   ```

3. **Verify Rollback**
   ```bash
   # Check feature flag disabled
   curl -s http://localhost:8000/health | jq '.features.rag_plus_plus.enabled'
   # Expected: false

   # Verify RAG mode (no reranking)
   grep "rag_mode" logs/rag.log | tail -5
   # Expected: mode=rag (not rag_plus_plus)
   ```

4. **Monitor Metrics**
   - Check `rag_rerank_duration_seconds` counter stops increasing
   - Check `rag_retrieval_latency_seconds{mode="rag"}` returns to baseline
   - Verify user complaints stop

5. **Create Incident Report**
   - Document trigger condition
   - Root cause analysis
   - Timeline of events
   - Remediation plan for re-enabling

6. **Post-Mortem**
   - Schedule meeting within 24 hours
   - Identify improvements (config, monitoring, testing)
   - Update runbook with lessons learned

---

## 📞 Escalation

### On-Call Contact

**Primary**: Tech Lead (Epic 21 owner)
**Secondary**: AI Architect (design decisions)
**Escalation**: Engineering Manager (product decisions)

### Incident Severity

| Severity | Condition | Response Time | Escalation |
|----------|-----------|---------------|------------|
| **P0** | Service down, data loss | Immediate | Manager + CTO |
| **P1** | Latency >10s, crash rate >5% | <15 min | Tech Lead |
| **P2** | Win rate <50%, fallback >10% | <1 hour | Tech Lead |
| **P3** | High variance, minor issues | <4 hours | On-call |

---

## 📚 References

- [Architecture Vision](./ARCHITECTURE_VISION.md)
- [Interfaces & Contracts](./INTERFACES_CONTRACTS.md)
- [MADR 0001](./decisions/0001-reranker-architecture.md)
- [Stage 21_04 Report](./stage_21_04_report.md) (after validation)
- [Prometheus Queries](https://prometheus.internal/graph)
- [Grafana Dashboard](https://grafana.internal/d/rag-plus-plus)

---

## ✅ Operational Checklist

**Pre-Deployment** (Stage 21_03):
- [ ] Config file reviewed and approved
- [ ] Feature flag set to `false` (default)
- [ ] Metrics exported and visible in Grafana
- [ ] Rollback procedure tested (integration test)
- [ ] On-call team trained on runbook

**Post-Deployment** (Stage 21_04):
- [ ] Monitor latency for 24 hours (baseline)
- [ ] Run manual evaluation (win rate)
- [ ] Review fallback rate (<5%)
- [ ] Update MADR with production results
- [ ] Schedule feature flag enable (if validation passes)

---

**Version**: 1.0
**Last Updated**: 2025-11-12
**Next Review**: After Stage 21_04 (post-validation)
