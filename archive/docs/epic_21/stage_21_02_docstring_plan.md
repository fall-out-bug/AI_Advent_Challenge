# Stage 21_02 · Docstring & Lint Plan

## Objective
Align repository documentation with the mandated docstring template and enforce
automated linting workflows that catch violations early.

## Template Enforcement
- Adopt the docstring structure from `.cursor/rules/cursorrules-unified.md` with pragmatic Option B rules (see `architect/docstring_faq.md`). Option B is now the mandated standard for Epic 21 and onward:
  ```
  """Brief summary.

  Purpose:
      ...

  Args:
      ...

  Returns:
      ...

  Raises:
      ...

  Example:
      >>> ...
  """
  ```
- Apply to all public classes/functions across `src/`, `shared/`, and `packages/`.
- Record exceptions (internal helpers, dunder methods) with justification in module comments.

## Gap Analysis
- **ContextManager** docstrings omit `Purpose` and `Example` sections.  
  ```1:82:src/application/services/context_manager.py
  def create_summary(...):
      """Create summary of old messages."""
  ```
- **ReviewSubmissionUseCase** helper methods lack docstrings entirely despite being public within class.
- Several infrastructure adapters expose public APIs without proper documentation (pending detailed audit).

## Linting Enhancements
1. **Pre-commit Hooks**
   - Add hooks for Black (line length 88), isort, flake8, mypy, pydocstyle (Google conventions), and markdownlint.
2. **`make lint` Target**
   - Aggregate tool invocations; ensure exit codes bubble up.
3. **CI Updates**
   - Mirror `make lint` in GitHub Actions; fail builds on docstring/pydocstyle errors.

## Work Breakdown
| Task ID | Description | Owner | Dependencies |
|---------|-------------|-------|--------------|
| DOC-21-02-01 | Generate docstring coverage report (pydocstyle + custom script) | Docs Lead | Stage 21_01 module moves |
| DOC-21-02-02 | Update core modules (`domain`, `application`) with full template | Domain/App teams | DOC-21-02-01 |
| DOC-21-02-03 | Expand to `infrastructure`, `presentation`, `workers` | Cross-team | After DOC-21-02-02 |
| DOC-21-02-04 | Configure pre-commit + CI lint | DevEx | Coordination with DevOps |
| DOC-21-02-05 | Document lint workflow in `CONTRIBUTING.md` | Docs Lead | After tooling merged |

## Acceptance Criteria
- No pydocstyle violations in CI.
- All new/updated modules include examples demonstrating usage.
- Contributors can run `make lint` and `pre-commit run --all-files` with deterministic output.


