# Pre-Commit Strategy · Epic 21

**Purpose**: Define staged rollout of pre-commit hooks to balance code quality with developer velocity.

**Status**: Draft (awaiting Tech Lead decision on Option A/B/C)

---

## Problem Statement

**From Tech Lead feedback**:
> Подключение `mypy`, `bandit`, `markdownlint` на каждый коммит может серьёзно замедлить цикл.

**Current Pain Points**:
- Full hook suite takes ~30s per commit
- Developers frustrated with slow feedback loop
- Risk: developers bypass hooks with `--no-verify`

**Goal**: Fast local commits (<5s) + comprehensive CI checks.

---

## Proposed Options

### Option A: All Hooks Mandatory (Strict)

**Configuration**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict, --ignore-missing-imports]
  
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-r, src/, -ll]  # Low severity threshold
  
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.37.0
    hooks:
      - id: markdownlint
        args: [--fix]
```

**Execution Time**: ~30s per commit

**Pros**:
- ✅ Maximum quality enforced locally
- ✅ Catches issues before push
- ✅ Uniform across all developers

**Cons**:
- ❌ Slow feedback loop
- ❌ Developers may bypass with `--no-verify`
- ❌ Friction for quick fixes

---

### Option B: Fast Auto, Slow Manual (Recommended)

**Configuration**:
```yaml
# .pre-commit-config.yaml

# Default stage: commit (runs on every git commit)
default_stages: [commit]

repos:
  # --- FAST HOOKS (auto on every commit) ---
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11
        # Timing: ~1s
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        # Timing: ~1s
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]
        # Timing: ~3s
  
  # --- SLOW HOOKS (manual, before push) ---
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        stages: [manual]  # ← Only run via explicit command
        additional_dependencies: [types-all]
        args: [--strict, --ignore-missing-imports]
        # Timing: ~15s
  
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        stages: [manual]  # ← Only run via explicit command
        args: [-r, src/, -ll]
        # Timing: ~10s
  
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.37.0
    hooks:
      - id: markdownlint
        stages: [manual]  # ← Only run via explicit command
        args: [--fix]
        # Timing: ~5s
```

**Usage**:

```bash
# Regular commit (fast hooks only)
git add src/domain/agents/butler_orchestrator.py
git commit -m "refactor: extract dialog context repository"
# Runs: black, isort, flake8 (~5s)

# Before push (run manual hooks explicitly)
pre-commit run --hook-stage manual --all-files
# Runs: mypy, bandit, markdownlint (~30s)

# Or configure git pre-push hook to run manual stage automatically
# (see setup instructions below)
```

**Execution Time**: 
- Commit: ~5s (fast)
- Pre-push: ~30s (manual hooks)

**Pros**:
- ✅ Fast commit loop (encourages frequent commits)
- ✅ Comprehensive checks before push
- ✅ CI always runs all hooks (safety net)

**Cons**:
- ⚠️ Developers might forget to run manual hooks
- ⚠️ Requires discipline (or pre-push automation)

---

### Option C: Gradual Rollout

**Week 1-2**: Black + isort only
```yaml
repos:
  - repo: https://github.com/psf/black
    hooks: [{id: black}]
  - repo: https://github.com/pycqa/isort
    hooks: [{id: isort}]
```

**Week 3-4**: Add flake8
```yaml
repos:
  # ... black, isort ...
  - repo: https://github.com/pycqa/flake8
    hooks: [{id: flake8}]
```

**Week 5+**: Add mypy/bandit (manual stage)
```yaml
repos:
  # ... black, isort, flake8 ...
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks: [{id: mypy, stages: [manual]}]
  - repo: https://github.com/PyCQA/bandit
    hooks: [{id: bandit, stages: [manual]}]
```

**Pros**:
- ✅ Team adapts gradually
- ✅ Lower initial friction

**Cons**:
- ❌ Long timeline (5+ weeks)
- ❌ Inconsistent quality during rollout

---

## Recommendation: Option B

**Rationale**:
1. **Developer experience**: Fast commits (<5s) don't break flow
2. **Quality gate**: Manual hooks catch issues before push
3. **CI safety net**: All hooks run in CI (comprehensive check)
4. **Proven pattern**: Used successfully in large projects (e.g., Django)

---

## Implementation Guide (Option B)

### Step 1: Install pre-commit

```bash
# Install pre-commit package
poetry add --group dev pre-commit

# Or via pip
pip install pre-commit
```

### Step 2: Create `.pre-commit-config.yaml`

```yaml
# .pre-commit-config.yaml (Epic 21)

default_stages: [commit]

repos:
  # Fast hooks (auto)
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile, black]  # Compatible with Black
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args:
          - --max-line-length=88
          - --extend-ignore=E203,W503
          - --exclude=archive/,htmlcov/,var/
  
  # Slow hooks (manual)
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        stages: [manual]
        additional_dependencies:
          - types-requests
          - types-PyYAML
        args:
          - --strict
          - --ignore-missing-imports
          - --exclude=archive/
  
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        stages: [manual]
        args:
          - -r
          - src/
          - -ll  # Low-low severity threshold
          - --skip=B101,B601  # Skip assert, shell=True warnings
  
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.37.0
    hooks:
      - id: markdownlint
        stages: [manual]
        args: [--fix, --ignore, node_modules/, --ignore, archive/]
```

### Step 3: Install hooks

```bash
# Install pre-commit hooks (runs automatically before git commit)
pre-commit install

# Expected output:
# pre-commit installed at .git/hooks/pre-commit
```

### Step 4: (Optional) Install pre-push hook

```bash
# Create .git/hooks/pre-push script
cat > .git/hooks/pre-push <<'EOF'
#!/bin/bash
# Run manual pre-commit hooks before push

echo "Running pre-push checks (mypy, bandit, markdownlint)..."
pre-commit run --hook-stage manual --all-files

if [ $? -ne 0 ]; then
    echo "❌ Pre-push checks failed. Fix issues before pushing."
    echo "Or skip with: git push --no-verify"
    exit 1
fi

echo "✅ Pre-push checks passed."
EOF

chmod +x .git/hooks/pre-push
```

### Step 5: Update `.gitignore`

```gitignore
# .gitignore additions
.pre-commit-cache
```

---

## Developer Workflows

### Workflow 1: Regular Commit (Fast)

```bash
# Edit code
vim src/domain/agents/butler_orchestrator.py

# Stage changes
git add src/domain/agents/butler_orchestrator.py

# Commit (fast hooks run automatically)
git commit -m "refactor: extract dialog context repository"

# Output:
# black....................................................................Passed
# isort....................................................................Passed
# flake8...................................................................Passed
# [main abc123] refactor: extract dialog context repository
#  1 file changed, 10 insertions(+), 5 deletions(-)

# Time: ~5 seconds
```

### Workflow 2: Pre-Push Check (Manual)

```bash
# Before pushing, run manual hooks
pre-commit run --hook-stage manual --all-files

# Output:
# mypy.....................................................................Passed
# bandit...................................................................Passed
# markdownlint.............................................................Passed

# Time: ~30 seconds

# Now push
git push origin feature/arch-21-01
```

### Workflow 3: Fix Specific Issue

```bash
# Run specific hook
pre-commit run mypy --all-files

# Or just on staged files
pre-commit run mypy
```

### Workflow 4: Skip Hooks (Emergency Only)

```bash
# Skip all hooks (use with caution!)
git commit --no-verify -m "hotfix: critical bug"

# Note: CI will still run all hooks
```

---

## CI Integration

### GitHub Actions

```yaml
# .github/workflows/ci.yml

lint:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install pre-commit
      run: pip install pre-commit
    
    - name: Cache pre-commit hooks
      uses: actions/cache@v3
      with:
        path: ~/.cache/pre-commit
        key: pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}
    
    - name: Run fast hooks
      run: pre-commit run --all-files
    
    - name: Run manual hooks (mypy, bandit)
      run: pre-commit run --hook-stage manual --all-files
```

**Key points**:
- CI runs **all** hooks (fast + manual)
- Cache pre-commit environments for speed
- Separate steps for visibility

---

## Troubleshooting

### Issue: "pre-commit not found"

```bash
# Install pre-commit
poetry add --group dev pre-commit

# Or globally
pip install --user pre-commit
```

### Issue: "Hooks too slow even for fast ones"

```bash
# Run only on changed files (not --all-files)
pre-commit run

# Or skip specific slow hooks
SKIP=flake8 git commit -m "WIP: temp commit"
```

### Issue: "mypy reports errors in venv"

```yaml
# Update .pre-commit-config.yaml to exclude venv
- id: mypy
  args:
    - --exclude=venv/|.venv/|archive/
```

### Issue: "Bandit false positives"

```yaml
# Skip specific checks via args
- id: bandit
  args:
    - --skip=B101,B601  # Skip assert, shell=True
```

Or inline in code:
```python
# nosec: B101
assert user_id, "user_id required"
```

---

## Metrics to Track

After 2 weeks of Option B deployment:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Average commit time | <10s | Developer survey |
| Hooks bypassed (--no-verify) | <5% | Git log analysis |
| CI failures due to linting | <10% | CI logs |
| Developer satisfaction | >7/10 | Survey |

---

## Migration Plan

### Phase 1: Install (Week 1 of Stage 21_00)

- [ ] Add `.pre-commit-config.yaml` to repo (Option B config)
- [ ] Update `README.md` with setup instructions
- [ ] Team training session (30 min)

### Phase 2: Soft Launch (Week 1-2 of Stage 21_01)

- [ ] Optional for developers (not enforced)
- [ ] CI runs all hooks (enforcement)
- [ ] Collect feedback

### Phase 3: Mandatory (Week 3+ of Stage 21_01)

- [ ] Enforce in CI (block merge if hooks fail)
- [ ] Developers must install hooks
- [ ] Monitor metrics

---

## Decision Matrix

| Criterion | Option A | Option B | Option C |
|-----------|----------|----------|----------|
| Commit speed | 🔴 Slow (30s) | 🟢 Fast (5s) | 🟢 Fast (gradual) |
| Quality enforcement | 🟢 High | 🟡 Medium | 🟡 Medium (ramps up) |
| Developer satisfaction | 🔴 Low | 🟢 High | 🟡 Medium |
| Setup complexity | 🟢 Simple | 🟡 Medium | 🔴 Complex (phased) |
| Time to full rollout | 🟢 Immediate | 🟢 Immediate | 🔴 5+ weeks |

**Architect recommendation**: **Option B** (fast auto, slow manual)

---

## Decision Required from Tech Lead

- [ ] **Option A**: All hooks mandatory (strict, slow)
- [ ] **Option B**: Fast auto, slow manual (recommended)
- [ ] **Option C**: Gradual rollout (phased)

**Please choose one option**. Will update Stage 21_02 tooling plan accordingly.

---

## References

- **Pre-commit Docs**: https://pre-commit.com/
- **Stage 21_02**: `stage_21_02_tooling_rollout.md`
- **Repo Rules**: Clean Code Practices (fast feedback loops)

---

**Document Owner**: EP21 Architect + DevEx  
**Status**: Draft (awaiting Tech Lead decision)  
**Last Updated**: 2025-11-11

