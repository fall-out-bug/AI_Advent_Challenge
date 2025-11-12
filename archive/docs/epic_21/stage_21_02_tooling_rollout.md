# Stage 21_02 · Tooling Rollout Plan

## Timeline
| Week | Focus | Deliverables |
|------|-------|--------------|
| W1 | Baseline inventory | List current linting/formatting tools, identify gaps |
| W2 | Configure tooling | Update `pyproject.toml`, add pre-commit hooks, adjust `Makefile` |
| W3 | Pilot run | Apply tools to small subset of modules, fix reported issues |
| W4 | Full rollout | Run `pre-commit run --all-files`, resolve outstanding violations, merge CI updates |

## Toolchain
- **Black**: code formatting (`line-length = 88`)
- **isort**: import sorting (`profile = black`)
- **flake8**: style & complexity (`max-line-length = 88`, enable docstring checks)
- **mypy**: static typing (strict optional, disallow untyped defs where feasible)
- **pydocstyle**: enforce docstring template (Google style)
- **bandit**: security checks (targeted runs on infrastructure/presentation)
- **markdownlint**: documentation consistency (`docs/`, `README*`)

## Pre-commit Configuration (Option B — fast hooks mandatory, heavy hooks manual)
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort
  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.1
    hooks:
      - id: mypy
        stages: [manual]
  - repo: https://github.com/pycqa/pydocstyle
    rev: 6.3.0
    hooks:
      - id: pydocstyle
  - repo: https://github.com/DavidAnson/markdownlint-cli2
    rev: v0.11.0
    hooks:
      - id: markdownlint-cli2
        stages: [manual]
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.9
    hooks:
      - id: bandit
        stages: [manual]
```

## CI Integration
- Update GitHub Actions workflow to execute (all hooks, including manual stages):
  - `make lint`
  - `pytest --cov=src --cov=shared --cov=packages`
  - `bandit -r src/ infrastructure/`
- Upload coverage reports to artifact for review.
- Fail CI if lint violations or coverage < 80%.

## Communication
- Announce tooling changes via repository README and change log.
- Provide quick-start snippet:
  ```bash
  pip install pre-commit
  pre-commit install
  pre-commit run --all-files
  ```
- Document remediation tips (e.g., how to auto-fix docstrings, run mypy with `--ignore-missing-imports` during migration).

## Risk Mitigation
- Run tools in dry-run mode before enabling blocking behavior.
- Allow temporary `per-file-ignores` for legacy modules, tracked in separate backlog.
- Ensure formatting changes merged promptly to avoid drift.


