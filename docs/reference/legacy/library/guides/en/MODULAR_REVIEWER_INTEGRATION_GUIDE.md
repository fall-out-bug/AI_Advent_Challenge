# Modular Reviewer Integration Guide

This document describes how to consume the reusable `multipass-reviewer` package from another project. It assumes you want to integrate the modular multi-pass reviewer into an existing Clean Architecture codebase and reuse the shared infrastructure described in the AI Challenge repository.

## 1. Installation

### Option A. Poetry Path Dependency (monorepo)

1. Copy/checkout `packages/multipass-reviewer/` into your workspace (or add it as a git submodule).
2. Extend your `pyproject.toml`:

```toml
[tool.poetry.dependencies]
multipass-reviewer = { path = "packages/multipass-reviewer", develop = true }
```

3. Run `poetry install`.

### Option B. Poetry Git Dependency (remote consumption)

If you publish the package to a Git repository (tagged `v0.3.0`):

```toml
[tool.poetry.dependencies]
multipass-reviewer = { git = "https://example.com/multipass-reviewer.git", tag = "v0.3.0" }
```

Then execute `poetry install`.

The package requires Python 3.10+, `httpx 0.27`, and `prometheus-client 0.20`. Poetry will resolve these automatically when the dependency is declared.

### Stage 01_03 Hardening Snapshot

The `0.3.0` release (Stage 01_03) ships with:
- Strict lint/type gates (flake8 + mypy) on reviewer-critical modules.
- Expanded integration/unit coverage (≥94% package, ≥90% shared SDK).
- Permanent modular reviewer activation (kill-switch removed).

## 2. Environment Variables

Configure the shared infrastructure endpoints in `.env` (or your secrets manager):

```
MONGODB_URL=mongodb://admin:<password>@shared-mongo:27017/butler?authSource=admin
LLM_URL=http://llm-api:8000
LLM_MODEL=qwen
PROMETHEUS_URL=http://shared-prometheus:9090
```

- `LLM_MODEL` should be the alias (`qwen`, `mistral`, etc.). The reviewer normalises long model names, but aliases avoid validation errors.
- The modular reviewer is permanently enabled starting with version `0.3.0`; no runtime flag toggle is required.

## 3. Wiring the Service

Inside your application layer, create a bridge similar to `src/application/services/modular_review_service.py`:

```python
from multipass_reviewer.application.config import ReviewConfigBuilder
from multipass_reviewer.application.orchestrator import MultiPassReviewerAgent
from multipass_reviewer.domain.interfaces.archive_reader import ArchiveReader
from multipass_reviewer.domain.interfaces.llm_client import LLMClientProtocol
from multipass_reviewer.domain.interfaces.review_logger import ReviewLoggerProtocol

class ZipArchiveAdapter(ArchiveReader):
    def __init__(self, archive_service):
        self._archive_service = archive_service

    async def read_latest(self, archive_path: str, *_a, **_kw):
        submission = self._archive_service.extract_submission(archive_path, "sub")
        return submission.code_files

def _normalise_model(name: str) -> str:
    return name.lower().split(" ")[0].split("-")[0]

class LLMClientAdapter(LLMClientProtocol):
    def __init__(self, client: LLMClientProtocol, default_model: str) -> None:
        self._client = client
        self._default = _normalise_model(default_model)

    async def make_request(self, model_name: str, prompt: str, **kwargs):
        model = self._default if model_name == "summary" else self._default
        return await self._client.make_request(model, prompt, **kwargs)

class ModularReviewService:
    def __init__(self, archive_service, diff_analyzer, llm_client, review_logger):
        settings = get_settings()
        archive_adapter = ZipArchiveAdapter(archive_service)
        llm_adapter = LLMClientAdapter(llm_client, settings.llm_model)
        config = (
            ReviewConfigBuilder()
            .with_language("python")
            .with_static_analysis(["linter", "type_checker"])
            .enable_haiku()
            .build()
        )
        self._reviewer = MultiPassReviewerAgent(
            archive_reader=archive_adapter,
            llm_client=llm_adapter,
            logger=review_logger,
            config=config,
        )

    async def review_submission(self, new_archive, previous_archive, assignment_id, student_id):
        report = await self._reviewer.review_from_archives(
            new_archive_path=new_archive,
            previous_archive_path=previous_archive,
            assignment_id=assignment_id,
            student_id=student_id,
        )
        return report
```

Key points:
- Use the provided adapters to convert your infrastructure services into the package interfaces.
- `ReviewLogger` from AI Challenge already supports `trace_id` for correlating metrics/logs.
- Prometheus metrics are exported automatically via `multipass_reviewer.infrastructure.monitoring.metrics`.

## 4. Handling Errors & Metrics

- Every review pass now returns `status`/`error` metadata. Persist these fields or propagate them to clients.
- Tenacity retry/backoff is built in. Examine logs tagged with `trace_id` for failures.
- Call `observe_pass` (see `src/infrastructure/monitoring/checker_metrics.py`) if you need to record checker metrics downstream.

## 5. Tests

Reuse the integration/unit suites from AI Challenge to verify your wiring:

```bash
poetry run pytest tests/integration/test_modular_review_service.py -v
poetry run pytest tests/unit/application/services/test_modular_review_service.py -v
```

These tests demonstrate:
- Happy path review with fake LLM
- Custom configuration support
- Real LLM compatibility (skip if `LLM_URL` not set)
- Negative cases (archive extraction failure, package-level errors)

## 6. Benchmarking (Optional)

Use the inline benchmarking helper to measure latency:

```bash
LLM_URL=http://127.0.0.1:8000 \
LLM_MODEL=qwen poetry run python - <<'PY'
# helper measuring ModularReviewService.review_submission with dummy vs real LLM
# see docs/guides/en/USER_GUIDE.md in AI Challenge for the full script
PY
```

Latest measurements (Qwen/Qwen1.5-4B-Chat):
- Dummy LLM: avg 0.00068s (3 runs)
- Real LLM via `/v1/chat/completions`: avg 4.08s (5 runs)

Store the results in your own documentation to watch regressions.

## 7. Checklist for Other Projects

1. Add dependency (`path` or `git tag`).
2. Wire the adapters (`ArchiveReader`, `LLMClient`, `ReviewLogger`).
3. Configure env variables (`MONGODB_URL`, `LLM_URL`, `LLM_MODEL`, Prometheus).
4. Run unit/integration tests.
5. (Optional) Benchmark and monitor metrics.

The modular reviewer is now ready to be invoked from your use case layer just like in AI Challenge.
