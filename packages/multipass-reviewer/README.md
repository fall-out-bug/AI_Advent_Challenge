# Multipass Reviewer

Clean Architecture, plugin-based implementation of the multi-pass code review agent. The package exposes domain/application/infrastructure layers with configurable checkers, prompt resources, and optional Dockerized API deployment.

## Layout

```
multipass_reviewer/
├── domain/               # Pure domain logic (no infra imports)
├── application/          # Orchestrators, config, registry
├── infrastructure/       # Checkers, adapters, loaders
├── presentation/         # API/CLI wrappers
└── prompts/              # Embedded prompt templates
```

## Development

```bash
cd packages/multipass-reviewer
poetry install --with dev
poetry run pytest --cov=multipass_reviewer --cov-fail-under=90
poetry run mypy multipass_reviewer --strict
```

## Extras

- `static-analysis`: installs lint/typing toolchain for checker implementations.
- `mlops`: optional ML pipeline dependencies.
- `data`: optional data engineering dependencies.

## Status

Initial scaffolding; implementation to follow via TDD per project plan.
