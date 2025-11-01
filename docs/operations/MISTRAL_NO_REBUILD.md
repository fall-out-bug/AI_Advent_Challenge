# Update Mistral Model Without Rebuild

This guide switches the served Mistral model using environment variables and a container restart only.

## Prerequisites
- Container exposes a local OpenAI-compatible API.
- `MODEL_NAME` is read by the service (see `local_models/chat_api.py`).
- Optional: `HF_TOKEN` configured for gated models.

## Steps
1. Set the target model name, e.g. in compose/env:
   - `MODEL_NAME=mistralai/Mistral-7B-Instruct-v0.3`
   - Optionally set `HF_TOKEN=<your_hf_token>`
2. Persist model weights cache across restarts by bind-mounting host cache to the container path `/root/.cache/huggingface`.
3. Restart only the model service to reload weights (no image rebuild):
   ```bash
   docker compose up -d --no-deps --force-recreate mistral
   ```
4. Verify health and a quick smoke:
   ```bash
   curl -s http://localhost:8001/health
   curl -s -X POST http://localhost:8001/chat -H 'content-type: application/json' \
     -d '{"messages":[{"role":"user","content":"ping"}],"max_tokens":16}'
   ```

## Rollback
- Revert `MODEL_NAME` to previous value and repeat the restart step.

## Notes
- Agent function-calling uses:
  - `LLM_CHAT_BASE_URL` (default `http://localhost:8001/v1`)
  - `LLM_CHAT_MODEL` (e.g., `mistral-7b-instruct`)
- Keep low temperature (0.2) for reliable tool selection.
