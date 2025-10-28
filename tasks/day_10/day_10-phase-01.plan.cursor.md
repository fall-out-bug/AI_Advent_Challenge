<!-- 6cf1b895-cf7e-43fc-86ec-f8c6c6a9e7b2 e3c25705-b5a8-40c5-be2f-5423e0df49f2 -->
# Phase 1 Plan — Compatibility-First: Extend Existing MCP + SDK with local_models GPU Runtime

## Scope

- Use existing GPU-enabled `local_models` runtime for both StarCoder2-7B and Mistral-7B
- Implement 3 MCP tools: `formalize_task`, `generate_code`, `review_code`
- Wire MCP server and agent to call `local_models` (no new model Docker)
- Minimal but meaningful tests and docs

## Integration Approach

- Prefer calling `local_models/chat_api.py` HTTP endpoints (or import as Python module if run in-process)
- Standardize env vars:
- `STARCODER_ENDPOINT` (e.g., http://localhost:8001/chat)
- `MISTRAL_ENDPOINT` (e.g., http://localhost:8002/chat)
- `MODEL_TIMEOUT_SECONDS` (e.g., 60)
- Define thin inference adapters that translate prompts and parse responses

## Deliverables
- MCP server container image (Dockerfile) and compose service with env wiring
- Healthcheck for MCP server container (tool discovery smoke)

- Project skeleton (src/, config/, tests/, scripts/, examples/)
- Working MCP server exposing 3 tools over stdio and using `STARCODER_ENDPOINT`
- Mistral agent orchestrator using `MISTRAL_ENDPOINT`
- Initial pytest suite (smoke + unit for tool contracts)

## Files to Create/Update

- `mcp_server/src/server/starcoder_server.py`: implement 3 tools; call `inference/starcoder_client.py`; structured JSON; error handling
- `mcp_server/src/inference/starcoder_client.py`: HTTP client for StarCoder endpoint (`generate(prompt, params)`) with retries/timeouts
- `mcp_server/src/prompts/*.py`: prompts for formalize/review/generate
- `mcp_server/config/server_config.yaml`: add endpoint/timeouts; remove direct HF model params
- `mcp_server/requirements.txt`: add `httpx` (or `requests`) for client; keep pydantic/logging
- `mistral_agent/src/orchestrator/chat_orchestrator.py`: implement `_call_mistral` via `inference/mistral_client.py`
- `mistral_agent/src/inference/mistral_client.py`: HTTP client for Mistral endpoint (`complete(prompt, params)`) with retries/timeouts
- `examples/demo_workflow.py`: run 2 short scenarios end-to-end
- Tests:
- `mcp_server/tests/test_tools_smoke.py` (mock `starcoder_client`)
- `mistral_agent/tests/test_orchestrator_smoke.py` (mock `mistral_client`)

## Implementation Notes

- Keep functions ≤15 lines; move I/O and inference into clients
- Strict JSON schemas for tool outputs; validate via pydantic models
- Deterministic defaults: low temperature for tools
- Robust error handling: timeouts, HTTP errors, schema validation
- Logging: structured JSON for requests/latency/errors (no secrets)

## Validation

- `tools/list` exposes 3 tools; simple calls succeed against running `local_models`
- Agent single-step gen and review work
- `pytest -q` runs smoke tests; tests stub HTTP clients for determinism

## Runbook

1. Start `local_models` (existing): `docker-compose up -d` in `/home/fall_out_bug/studies/AI_Challenge/local_models`
2. Export endpoints:

- `export STARCODER_ENDPOINT=http://localhost:8001/chat`
- `export MISTRAL_ENDPOINT=http://localhost:8002/chat`

3. Start server: `make start-server`
4. Start agent: `make start-agent`
5. Run demo: `make demo`

## Risks/Mitigations

- Endpoint schema drift: lock a minimal request/response contract in clients and adaptors; unit-test parsers
- Latency: add short-circuit `max_tokens`/low `temperature`; tune timeouts
- Coverage: tests mock HTTP clients to reach 80%+ without heavy inference

### To-dos

- [ ] Create server/agent structure and HTTP inference clients
- [ ] Implement formalize_task using StarCoder prompt + schema
- [ ] Implement generate_code with StarCoder client
- [ ] Implement review_code with dynamic prompt and parsing
- [ ] Implement local Mistral client and wire _call_mistral
- [ ] Add server smoke tests for three tools (mock client)
- [ ] Add agent orchestrator smoke test (mock client)
- [ ] Update demo_workflow to run two scenarios
- [ ] Update README with Phase 1 usage and env endpoints