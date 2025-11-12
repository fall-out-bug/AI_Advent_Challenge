# Stage 21_02 · Code Quality & Rule Enforcement

## Goal
Ensure all modules comply with the unified Cursor rules by enforcing function-size
guidelines, harmonising docstrings and type hints, and codifying automatic tooling
to prevent regressions.

## Current Findings
- Several orchestrators and services exceed the recommended 15-line function guidance
  and 40-line maximum, reducing readability and reuse.
- Docstrings across domain/application layers omit the required `Purpose`,
  `Args`, `Returns`, `Raises`, and `Example` sections, limiting developer onboarding
  and documentation automation.
- Presentation and worker modules mix side-effectful IO and formatting logic without
  clear abstractions, complicating testability and mocking.

### Evidence Snapshot
- `src/application/use_cases/review_submission_use_case.py` contains methods such as
  `_append_log_analysis` (~30 LOC) and `_persist_report` (~25 LOC) that bundle logging,
  configuration, and persistence logic.
- `src/presentation/api/review_routes.py:create_review` handles validation, streaming IO,
  and invocation in a single coroutine, making linting and testing difficult.
- `src/application/services/context_manager.py` demonstrates the docstring template
  gap — sections exist but do not follow the mandated multi-paragraph structure.

## Planned Workstreams
1. **Function Decomposition & Helpers**
   - Identify oversized functions and split them into composable helpers placed in
     appropriate modules (e.g. validators, mappers, publishers).
   - Adopt composition patterns to reduce reliance on inheritance-heavy agents.
2. **Docstring & Type Hint Harmonisation**
   - Apply the prescribed docstring template to every public symbol, adding concrete
     examples and explicit exception sections.
   - Extend static type checks (mypy) to cover newly factored helpers and add strict
     casts where required.
3. **Automated Tooling & Formatters**
   - Update `pyproject.toml` and `Makefile` targets to run Black (line length 88),
     isort, flake8, mypy, and docstring linters in a single `make lint`.
   - Introduce pre-commit hooks mirroring CI checks to catch regressions locally.

## Backlog Draft
| ID | Impact | Action | Owner | Notes |
|----|--------|--------|-------|-------|
| CODE-21-01 | High | Refactor `ReviewSubmissionUseCase` helpers into dedicated collaborator classes (rate limiter, log pipeline, publisher adapter) | Application team | Enables focused unit tests |
| CODE-21-02 | High | Wrap file handling in `review_routes` with storage service + validator modules | Presentation team | Coordinates with Stage 21_01 |
| CODE-21-03 | Medium | Apply docstring template repo-wide; add CI docstring checker | Docs team | Sequenced after architecture moves |
| CODE-21-04 | Medium | Configure `pyproject.toml` tooling (Black/isort/flake8/mypy/pydocstyle) and update `make lint` | DevEx | Needs operations sign-off |
| CODE-21-05 | Medium | Introduce helper utilities for Markdown escaping / message formatting in presentation layer | Presentation team | Supports handler refactor |

## Exit Criteria
- Oversized functions reduced to ≤15 lines where practical, ≤40 lines absolute.
- All public APIs include compliant docstrings and complete type annotations.
- `make lint` runs all configured tools without manual steps; CI enforces the same.
- Presentation IO logic abstracted behind services, enabling targeted tests.
- Tech lead and product owner sign off on quality gates after analytics/architecture review feedback addressed.


