# EP01 Stage 01_01 · Staged Lint Allowlist Plan

## 1. Scope

Initial enforcement coverage:
- `packages/multipass-reviewer/`
- `shared/shared_package/clients/` and `shared/shared_package/agents/`
- `src/application/services/modular_review_service.py`
- `src/application/use_cases/review_submission_use_case.py`

Remainder of repo stays in “legacy debt” bucket—violations allowed but tracked.

## 2. Linter Tooling

- Continue using `flake8` (style/logic) and `mypy` (typing). Optionally layer `ruff` later once debt paid down; not for Stage 01_02.
- Bandit remains informational until lint debt reduced; no change in scope.

## 3. Configuration Approach

Add dedicated lint config section (example for `pyproject.toml` or `setup.cfg`):

```
[tool.flake8]
max-line-length = 88
select = ["E", "F", "W"]
per-file-ignores =
    # Legacy debt (allow all for now)
    src/*:E501,F401,F841,W503
    tests/*:B101
# Allowlist enforcement
extend-exclude =
    !packages/multipass-reviewer/*
    !shared/shared_package/clients/*
    !shared/shared_package/agents/*
    !src/application/services/modular_review_service.py
    !src/application/use_cases/review_submission_use_case.py
```

Then run flake8 twice:
1. `flake8 --config pyproject.toml` (default) – fails only on allowlisted paths.
2. `flake8 --count --exit-zero` (legacy mode) – tracks total debt but doesn’t block CI.

For mypy:

```
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
no_implicit_optional = true

[tool.mypy-packages.multipass-reviewer.*]
strict = true

[tool.mypy-shared.shared_package.clients.*]
strict = true

[tool.mypy-src.application.services.modular_review_service]
strict = true

[tool.mypy-src.application.use_cases.review_submission_use_case]
strict = true
```

Remaining modules can retain relaxed settings; gradually expand strict coverage by adding new sections.

## 4. CI Wiring (Stage 01_02)

Add make targets:

```
make lint-allowlist:
    poetry run flake8 packages/multipass-reviewer \
        shared/shared_package/clients \
        shared/shared_package/agents \
        src/application/services/modular_review_service.py \
        src/application/use_cases/review_submission_use_case.py
    poetry run mypy packages/multipass-reviewer \
        shared/shared_package/clients \
        shared/shared_package/agents \
        src/application/services/modular_review_service.py \
        src/application/use_cases/review_submission_use_case.py

make lint-debt:
    poetry run flake8 --count --exit-zero src tests shared packages
```

CI runs `make lint-allowlist` (blocking) + `make lint-debt` (non-blocking metrics).

## 5. Milestones

- Stage 01_02: establish config, fix violations in allowlisted modules.
- Stage 01_03: expand allowlist to shared SDK orchestration modules + reviewer-related presentation layer.
- Post Stage 01_03: evaluate replacing flake8 with ruff or extend strict mypy to full shared SDK.

