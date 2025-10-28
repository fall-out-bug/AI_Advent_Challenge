# Setup Guide - Phase 4

## Quick Setup Options

### Option 1: Local Development (No Docker - Recommended)

Since some models require Hugging Face tokens, the easiest way to get started is to use your existing local models setup:

```bash
# 1. Start local models (if you already have them running)
cd local_models
docker-compose up -d

# 2. Wait for models to be ready
# Check: curl http://localhost:8001/health

# 3. Run the chat interface
make mcp-chat-streaming
```

### Option 2: Full Docker Setup (Requires HF Token)

If you want to run everything in Docker:

```bash
# 1. Create .env file with your HF token
echo "HF_TOKEN=your_token_here" > .env

# 2. Start all services
make docker-up-full

# 3. Run chat
make mcp-chat-streaming
```

## Troubleshooting

### Models Won't Start

**Error**: `401 Client Error: Unauthorized`

**Solution**: You need a Hugging Face token for gated models. Options:
1. Get token from https://huggingface.co/settings/tokens
2. Add to `.env`: `HF_TOKEN=your_token`
3. Or skip Docker and use local models

### Local Models Are Running

If you already have local models running, the chat will work immediately:

```bash
# Just run the chat (no Docker needed)
make mcp-chat-streaming
```

The chat interface connects to your local models at:
- http://localhost:8000 (Qwen)
- http://localhost:8001 (Mistral)
- http://localhost:8002 (TinyLlama)

## Recommended Workflow

For development/testing:

```bash
# Terminal 1: Start local models (already running?)
docker ps | grep chat

# Terminal 2: Run chat
make mcp-chat-streaming

# Try it:
You: Create a Fibonacci function
# ... see the magic happen!
```

This avoids Docker complexity during development while still testing Phase 4 features.

