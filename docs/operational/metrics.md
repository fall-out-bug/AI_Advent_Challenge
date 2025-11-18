# Operational Metrics Documentation

This document describes all Prometheus metrics exposed by the AI Challenge system.

## Personalization Metrics

### Profile Metrics

- `user_profile_reads_total` — Total profile reads
  - Labels: None
  - Type: Counter
  - Description: Incremented each time a user profile is read from MongoDB

- `user_profile_writes_total` — Total profile writes
  - Labels: None
  - Type: Counter
  - Description: Incremented each time a user profile is written to MongoDB

- `user_profile_read_duration_seconds` — Profile read latency
  - Labels: None
  - Type: Histogram
  - Buckets: [0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
  - Description: Time taken to read a user profile from MongoDB

### Memory Metrics

- `user_memory_events_total{role}` — Total memory events by role
  - Labels:
    - `role`: "user" or "assistant"
  - Type: Counter
  - Description: Total number of memory events stored (user messages and assistant replies)

- `user_memory_compressions_total` — Total memory compressions
  - Labels: None
  - Type: Counter
  - Description: Number of times memory compression has been triggered (>50 events)

- `user_memory_compression_duration_seconds` — Compression duration
  - Labels: None
  - Type: Histogram
  - Buckets: [1.0, 5.0, 10.0, 30.0, 60.0]
  - Description: Time taken to compress memory (summarize old events)

### Request Metrics

- `personalized_requests_total{source,status}` — Personalized requests by source and status
  - Labels:
    - `source`: "text" or "voice"
    - `status`: "success" or "error"
  - Type: Counter
  - Description: Total personalized requests processed

- `personalized_prompt_tokens_total` — Prompt token count
  - Labels: None
  - Type: Histogram
  - Buckets: [100, 500, 1000, 1500, 2000, 2500, 3000]
  - Description: Number of tokens in personalized prompts sent to LLM

### Alerts

The following Prometheus alerts are configured for personalization:

- `PersonalizationHighErrorRate` — >10% error rate in 5 minutes
  - Severity: Warning
  - Component: personalization
  - Runbook: Check logs for personalized_reply_use_case, verify LLM and MongoDB connectivity

- `MemoryCompressionHighDuration` — P95 compression duration >10s
  - Severity: Warning
  - Component: personalization
  - Runbook: Check logs for _compress_memory, verify LLM summarization working

## Butler Bot Metrics

See `docs/reference/en/MONITORING.md` for full Butler bot metrics documentation.

## MCP Server Metrics

See `docs/reference/en/MONITORING.md` for MCP server metrics documentation.

## Unified Worker Metrics

See `docs/reference/en/MONITORING.md` for unified worker metrics documentation.
