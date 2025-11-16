# Performance Benchmarks

## Day 10 MCP System Performance

### Latency Measurements

- **Tool Discovery:** <100ms (p95)
- **Single Tool Execution:** <30s (avg)
- **Multi-tool Workflow (3 steps):** <90s (avg)
- **Agent Intent Parsing:** <3s (p95)
- **Plan Generation:** <2s (avg)
- **Response Formatting:** <500ms (avg)

### Throughput

- **Concurrent Requests:** 5+ (tested)
- **Requests per minute:** 15 (sustained)
- **Cache Hit Rate:** 45%
- **Error Rate:** <1% (with retries)

### Resource Usage

- **Docker Image Size:** 1.2GB
- **Memory Baseline:** 512MB
- **Memory Peak (concurrent):** 2GB
- **CPU Usage:** 25% avg, 60% peak
- **Disk I/O:** <10MB/s

### Optimization Results

- **Result Caching:** 50% reduction in redundant calls
- **Plan Optimization:** 20% reduction in execution time
- **Context Management:** Zero token limit errors
- **Multi-stage Build:** 30% smaller image size

### Load Testing Results

#### Single User
- Average response time: 2.5s
- p95 response time: 5s
- p99 response time: 8s
- Success rate: 99.5%

#### Concurrent Users (5)
- Average response time: 4.2s
- p95 response time: 8s
- p99 response time: 12s
- Success rate: 98%

#### Stress Test (10 concurrent)
- Average response time: 8.5s
- p95 response time: 15s
- p99 response time: 20s
- Success rate: 95%

### Tool Performance Breakdown

| Tool | Avg Time | p95 | Calls/min |
|------|----------|-----|-----------|
| generate_code | 12s | 25s | 5 |
| review_code | 8s | 15s | 8 |
| generate_tests | 10s | 20s | 3 |
| format_code | 2s | 5s | 20 |
| analyze_complexity | 3s | 6s | 15 |
| formalize_task | 5s | 10s | 10 |

### Bottlenecks Identified

1. **Model Inference** - 80% of latency comes from LLM API calls
2. **Context Building** - 10% of latency from context preparation
3. **Network I/O** - 5% of latency from data transfer
4. **Serialization** - 5% of latency from JSON parsing

### Recommendations

1. Implement response streaming for better UX
2. Add more aggressive caching for common requests
3. Use async/await for parallel tool execution
4. Optimize context window management for long conversations
5. Consider model fine-tuning for domain-specific tasks

### Testing Methodology

All benchmarks were conducted with:
- Python 3.11
- Linux (WSL2)
- 16GB RAM
- 8 CPU cores
- Docker Desktop with 4GB memory allocation


## Day 18 Modular Reviewer Latency (2025-11-08)

### Review Pipeline

- **Dummy LLM (no external call)**: avg 0.00068s over 3 runs (perf helper script)
- **Qwen/Qwen1.5-4B-Chat via `/v1/chat/completions`**: avg 4.08s over 5 runs
- Benchmark script: see inline helper in `docs/guides/en/USER_GUIDE.md` (custom `RealLLMClient` hitting OpenAI-compatible endpoint)
- Metrics exported via Prometheus for pass/checker runtimes and LLM token usage

## Stage 05 Benchmarks (EP23 · 2025-11-15)

Stage 05 introduces RU summarisation quality benchmarks driven by LLM-as-judge
evaluations. Latest runs:

| Scenario | Dataset | Model | Coverage | Accuracy | Coherence | Informativeness | Latency (avg) | Outcome | Notes |
|----------|---------|-------|----------|----------|-----------|-----------------|---------------|---------|-------|
| Channel Digest (RU) – Dry-run | benchmark_digest_ru_v1 | GroundTruthJudge | 0.89 (warn) | 0.89 (warn) | 0.89 (warn) | 0.905 (pass) | 189.0s (pass) | WARN | CLI: `run_benchmark.py --scenario channel_digest_ru --dry-run` (2025-11-15). |
| Channel Digest (RU) – Live | benchmark_digest_ru_v1 | gpt-4o (via local LLM_URL) | 0.95 (pass) | 0.95 (pass) | 0.95 (pass) | 0.85 (warn) | 189.0s (pass) | WARN | `LLM_URL=http://127.0.0.1:8000 run_benchmark.py --scenario channel_digest_ru` (Stage 05_03 pilot). |
| Reviewer Summary (RU) | benchmark_review_ru_v1 | qwen-7b | TBD | TBD | TBD | TBD | TBD | Pending | Dataset export done; benchmark pending TL-03 follow-up. |

## Stage 06 Calibrated MCP Latency (2025-11-11)

Target thresholds now power the MCP performance tests (`tests/legacy/src/presentation/mcp/test_performance.py`).
Values are derived from five-run medians on CI using the new shared infra bootstrap scripts.

| Operation | Measured p95 (s) | Threshold (s) | Notes |
|-----------|------------------|---------------|-------|
| Tool discovery (`list_tools`) | 0.42 | 1.00 | Fast path via stdio client; unchanged. |
| Calculator tool (`add`) | 0.97 | **1.20** | Threshold exported as `MCP_CALCULATOR_LATENCY_P95_SEC`. |
| Token counter – small payload | 0.91 | **1.10** | Covers ≤10 tokens. |
| Token counter – medium payload | 1.04 | **1.30** | Covers ~100 tokens. |
| Token counter – large payload | 1.33 | **1.60** | Covers ~1,000 tokens. |
| Model listing (`list_models`) | 0.98 | **1.20** | Ensures catalog queries stay sub-second. |

> Thresholds match automation recorded in `.github/workflows/ci.yml` and serve as guardrails for future regressions.
