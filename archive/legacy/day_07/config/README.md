# Configuration Files

This directory contains configuration files for the StarCoder Multi-Agent System.

## Files

### `external_api_config.json`
Production configuration for external API providers (ChatGPT, Claude).

**Format:**
```json
{
  "providers": {
    "chatgpt": {
      "api_key": "your-openai-key",
      "base_url": "https://api.openai.com/v1",
      "models": ["gpt-3.5-turbo", "gpt-4"]
    },
    "claude": {
      "api_key": "your-anthropic-key", 
      "base_url": "https://api.anthropic.com",
      "models": ["claude-3-sonnet-20240229"]
    }
  },
  "default_provider": "chatgpt",
  "timeout": 30,
  "max_retries": 3
}
```

### `external_api_config.example.json`
Example configuration template for external API providers.

**Usage:**
1. Copy this file to `external_api_config.json`
2. Add your actual API keys
3. Modify settings as needed

### `env.traefik.example`
Environment variables template for Traefik reverse proxy deployment.

**Usage:**
1. Copy to `.env` in project root
2. Modify values as needed
3. Used with `docker-compose.traefik.yml`

## Security Notes

- **Never commit actual API keys** to version control
- Use environment variables for sensitive data
- Keep example files as templates only
- Rotate API keys regularly

## Environment Variables

For external APIs, set these environment variables:

```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

## Docker Configuration

For Docker deployments, use the appropriate docker-compose file:

- `docker-compose.yml` - Basic bridge network
- `docker-compose.bridge.yml` - Explicit bridge network  
- `docker-compose.traefik.yml` - Traefik reverse proxy

See `docs/DEPLOYMENT.md` for detailed deployment instructions.
