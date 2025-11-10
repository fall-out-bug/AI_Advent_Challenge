# Security Documentation

## Overview

This document describes security policies, practices, and guidelines for the AI Challenge project.

## Secrets Management

### Current State

- **API Keys**: Stored in `api_key.txt` (gitignored)
- **Environment Variables**: Stored in `.env` files (gitignored)
- **Git History**: Scanned for secrets - no secrets found in history ✓

### Best Practices

1. **Never commit secrets to git**
   - All secret files are in `.gitignore`
   - Pre-commit hook scans for secrets before commit

2. **Use environment variables**
   - Prefer environment variables over files
   - Use `.env.example` as template
   - Rotate keys regularly

3. **Secret Detection**
   - Pre-commit hook: `scripts/quality/check_secrets.sh`
   - Scans for common secret patterns
   - Blocks commits with potential secrets

### Rotating Secrets

If secrets are found in git history:

```bash
# 1. Scan history
git log --all --full-history -- api_key.txt

# 2. Remove from history (if found)
git filter-repo --path api_key.txt --invert-paths

# 3. Rotate all API keys
# - Perplexity API
# - ChadGPT API
# - Telegram Bot Token
# - HuggingFace Token

# 4. Force push (coordinate with team)
git push --force
```

## Docker Security

### Current Implementation

- ✅ Non-root users: `appuser`, `butler`, `worker`, `mcpuser`
- ✅ Multi-stage builds
- ✅ Healthchecks configured
- ✅ Minimal base images (`python:3.10-slim`)

### Improvements Needed

1. **Read-only filesystem**:
   ```dockerfile
   RUN --mount=type=tmpfs,target=/tmp
   ```

2. **Drop capabilities**:
   ```dockerfile
   RUN --security-opt=no-new-privileges:true
   ```

3. **Security scanning**:
   - Add `docker scan` to CI/CD
   - Use Trivy or Snyk for vulnerability scanning

## Network Security

### CORS Configuration

- FastAPI endpoints should have explicit CORS origins
- No wildcard (`*`) origins in production

### MongoDB Security

- Default credentials: **NEVER USE**
- Use authentication in production
- Network isolation in Docker networks

## API Key Loading

### Current Implementation

- File-based: `shared/config/api_keys.py`
- Environment variable fallback
- No encryption

### Recommendations

1. **Add encryption** for file-based storage
2. **Use vault integration** (HashiCorp Vault, AWS Secrets Manager)
3. **Add audit logging** for key access

## Pre-Commit Security Checks

Run before every commit:

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Manual check
scripts/quality/check_secrets.sh
```

## Security Scanning

### Bandit (Python Security Scanner)

```bash
bandit -r src/ -ll
```

### Docker Security Scan

```bash
docker scan ai-challenge:latest
```

## Incident Response

If secrets are exposed:

1. **Immediately rotate** all exposed keys
2. **Remove from git history** (if committed)
3. **Notify team** via secure channel
4. **Audit logs** for unauthorized access
5. **Document incident** in security log

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security.html)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
