# Cursor Rules Quick Reference & Implementation Guide

## 📊 The 13 Rules at a Glance

| # | Rule | File Types | Priority | Focus |
|---|------|-----------|----------|-------|
| 1 | **Python Zen Writer** | `*.py` | 🔴 High | Code style, readability, Zen of Python |
| 2 | **Python Code Reviewer** | `*.py` | 🟠 Medium | Type hints, logging, testing, frameworks |
| 3 | **Chief Architect** | `*.py`, `*.yaml` | 🔴 High | SOLID, layers, DI, architecture |
| 4 | **AI Reviewer** | Source code | 🟠 Medium | Token cost, function size, LLM-friendly |
| 5 | **Security Reviewer** | `*.py`, `*.yml`, `Dockerfile` | 🔴 High | Secrets, IAM, crypto, HTTPS, container security |
| 6 | **DevOps Engineer** | `Dockerfile`, `docker-compose`, CI/CD | 🔴 High | Monitoring, alerts, CI/CD, Docker best practices |
| 7 | **Technical Writer** | `README.md`, `docs/`, `*.py` | 🟠 Medium | Docstrings, API docs, CHANGELOG |
| 8 | **QA/TDD Reviewer** | `tests/**` | 🔴 High | Test coverage, unit/integration/E2E |
| 9 | **ML Engineer Reviewer** | `src/ml/**`, `*.py` | 🟡 Low* | Reproducibility, MLflow, metrics, versioning |
| 10 | **Data Engineer Reviewer** | `src/data/**`, `*.sql`, DAGs | 🟡 Low* | Schemas, lineage, ETL, data quality |
| 11 | **Docker Reviewer** | `Dockerfile*` | 🟠 Medium | Container security, layers, size |
| 12 | **Bash Reviewer** | `*.sh` | 🟡 Low | Shellcheck, security, readability |
| 13 | **Base Guide** | All files | 🔴 High | Global standards (PEP8, SOLID, DRY) |

*Low priority = triggered only for ML/Data-specific code

---

## 🎯 Rule Application Flow

### When you commit `src/domain/agents/butler_orchestrator.py`:

```
┌─────────────────────────────────────┐
│  File: butler_orchestrator.py       │
└─────────────────────────────────────┘
         ↓
    ┌────────────────────────────────┐
    │ Trigger: "class", "def", "import" │
    └────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────────────────────────────┐
    │ Rules Triggered (priority order):                           │
    │ 1. Python Zen Writer (style, readability)                  │
    │ 2. Chief Architect (SOLID, layers, DI)                    │
    │ 3. Security Reviewer (no secrets)                          │
    │ 4. Python Code Reviewer (types, logging, testing)          │
    │ 5. AI Reviewer (token cost, function length)               │
    └─────────────────────────────────────────────────────────────┘
         ↓
    ┌──────────────────────────────────────┐
    │ Cursor Review Output:                │
    │ ✅ Style OK (Zen Writer)             │
    │ ✅ Architecture OK (SOLID)           │
    │ ⚠️  Function >30 lines (AI Reviewer)  │
    │ ✅ No secrets found                  │
    │ ⚠️  Missing docstrings (Technical)   │
    └──────────────────────────────────────┘
```

---

## 🔄 Typical Cursor Suggestions

### Rule 1: Python Zen Writer
```
❌ ISSUE: lambda with 3-level nesting
✅ FIX: Split into named functions
```

### Rule 3: Chief Architect
```
❌ ISSUE: MongoDBClient depends on LLMClient (circular)
✅ FIX: Introduce interface; use Dependency Injection
```

### Rule 5: Security Reviewer
```
❌ ISSUE: API_KEY hardcoded in config.py
✅ FIX: Load from environment variable via .env
```

### Rule 6: DevOps Engineer
```
❌ ISSUE: No HEALTHCHECK in Dockerfile
✅ FIX: Add HEALTHCHECK with liveness probe
```

### Rule 8: QA/TDD Reviewer
```
❌ ISSUE: butler_orchestrator.py has 0 tests
✅ FIX: Create tests/unit/test_butler_orchestrator.py (target 80% coverage)
```

---

## 📝 How to Use `.cursorrules`

### 1. Copy the Unified Rules

```bash
# Copy from cursorrules-unified.md to .cursorrules
cp cursorrules-unified.md .cursorrules

# Or manually:
# 1. Open cursorrules-unified.md
# 2. Copy entire content
# 3. Create `.cursorrules` file in project root
# 4. Paste content
# 5. Save
```

### 2. Verify Cursor Recognizes It

```bash
# In Cursor IDE:
# - Open any .py file
# - Look for rule indicators in editor
# - Hover over suggestions to see which rule triggered
```

### 3. Configure Per-Rule Strictness (Optional)

Add at top of `.cursorrules`:

```yaml
ruleOverrides:
  PythonZenWriter:
    strictness: HIGH  # Always enforce
  AIReviewer:
    strictness: MEDIUM  # Warn if >40 lines, don't block
  SecurityReviewer:
    strictness: CRITICAL  # Always enforce, can block commit
```

---

## 🚀 Best Practices with Cursor Rules

### During Development

1. **Write code** → Cursor auto-suggests improvements
2. **Review suggestions** → Accept/ignore per rule
3. **Focus on red (🔴)** priority rules first
4. **Use medium (🟠)** rules for refinement
5. **Reference low (🟡)** rules when relevant

### Pre-Commit

Run this checklist:

```bash
# 1. Lint check (Python Zen Writer)
black src/
flake8 src/
mypy src/

# 2. Type check (Chief Architect)
# (mypy covers this)

# 3. Security scan (Security Reviewer)
bandit src/ --r

# 4. Tests (QA/TDD Reviewer)
pytest tests/ --cov=src/

# 5. Docker builds (DevOps Engineer)
docker build -t butler:latest .

# 6. Documentation (Technical Writer)
# Check all .py files have docstrings
```

### Commit Message Format (Conventional Commits)

```
feat(butler): implement dialog orchestrator
- Add FSM for multi-turn conversations
- Support 4 behavior modes: task, data, reminders, chat
- Add comprehensive logging and error handling

Fixes: #42
Review-by: Chief Architect, Python Zen Writer
```

---

## 🎓 Learning Cursor Rules

### Phase 1: Understand Core 3 Rules (Day 1)

1. **Python Zen Writer** — Learn how to write beautiful, readable code
2. **Chief Architect** — Understand SOLID and layered architecture
3. **Security Reviewer** — Never commit secrets!

### Phase 2: Add Test & DevOps (Day 2)

4. **QA/TDD Reviewer** — Write tests alongside code
5. **DevOps Engineer** — Set up monitoring and CI/CD

### Phase 3: Polish (Day 3+)

6. **Technical Writer** — Document well
7. **AI Reviewer** — Optimize for LLM tools
8. Others as needed

---

## 🔍 Rule Specifics by Category

### Code Quality (Rules 1-2)

**Python Zen Writer** checks:
- Function length (max 40 lines)
- Import grouping
- Type hints
- Docstring format

**Python Code Reviewer** checks:
- pandas/numpy usage
- HTTP error handling
- CLI argument parsing
- Test organization
- Logging consistency

### Architecture (Rules 3-4)

**Chief Architect** checks:
- SOLID principles
- Dependency Injection
- Layer separation
- Configuration externalization
- Design patterns

**AI Reviewer** checks:
- Token cost estimation
- Function decomposition
- Naming clarity
- Comment utility
- LLM chunk-ability

### Security & Ops (Rules 5-6)

**Security Reviewer** checks:
- Secret exposure
- IAM/RBAC
- Encryption (TLS, JWT)
- CORS policies
- Container security

**DevOps Engineer** checks:
- Docker image size/security
- CI/CD pipeline
- Prometheus metrics
- Grafana dashboards
- Alert templates

### Documentation & Testing (Rules 7-8)

**Technical Writer** checks:
- Docstring completeness
- README structure
- API documentation
- CHANGELOG format
- Examples accuracy

**QA/TDD Reviewer** checks:
- Unit test count
- Integration test logic
- E2E test coverage
- Mock usage
- Coverage ≥80%

### Specialized (Rules 9-13)

**ML Engineer** — Reproducibility, versioning, metrics
**Data Engineer** — Schema design, lineage, quality
**Docker Reviewer** — Container best practices
**Bash Reviewer** — Shell script security
**Base Guide** — Global standards (PEP8, SOLID, DRY)

---

## 🛠️ Troubleshooting

### "Cursor not showing suggestions"

→ Check `.cursorrules` exists in project root

→ Reload Cursor IDE

### "Too many suggestions from one rule"

→ Temporarily lower that rule's `strictness` setting

→ Or disable with `enabled: false`

### "Conflicting suggestions from 2 rules"

→ Follow priority order: 🔴 > 🟠 > 🟡

→ Or reference which rule in your comment: `# Rule 1: Python Zen`

### "My code style differs from rules"

→ Modify `.cursorrules` to match your preferences

→ Or argue in code comments: `# pylint: disable=...` (Cursor will note it)

---

## 📊 Metrics to Track

Track these after using Cursor rules for 2 weeks:

| Metric | Target | Current |
|--------|--------|---------|
| Code coverage | 80%+ | __ % |
| Lint pass rate | 100% | __ % |
| Security issues | 0 | __ |
| Function avg length | <20 lines | __ lines |
| Docstring coverage | 100% | __ % |
| Type hint coverage | 95%+ | __ % |
| CI/CD pass rate | 99%+ | __ % |

---

## 🎯 Your Next Steps

1. **Copy `cursorrules-unified.md` → `.cursorrules`**

2. **Reload Cursor IDE**

3. **Open `src/domain/agents/butler_orchestrator.py`** (or any file)

4. **Cursor will automatically suggest improvements** based on 13 rules

5. **Review suggestions** and accept/modify as needed

6. **Reference this guide** when unsure about a rule

---

## 📚 Full Rule Reference

For detailed rules, see:

- **cursorrules-unified.md** — Complete, ready-to-copy
- **Individual `.mdc` files** — Original versions (13 files in your project)

Choose unified (recommended) for consolidation or individual files for editing specific rules.

---

**Ready to code with Cursor rules! 🚀**
