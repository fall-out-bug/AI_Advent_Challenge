# Reviewer Day Capabilities

<<<<<<< HEAD
## Foundational Days 1-22

### Days 1-10 · Review Framework Setup
- Define review checklist templates (functionality, architecture, tests, ops).
- Configure reviewer log format with status tags and owners.
- Align with Analyst, Architect, Tech Lead on expected evidence packs.

### Day 11 · Shared Infra & MCP Baseline
- Validate shared infra readiness via smoke tests and logs.
- Confirm monitoring dashboards capture reviewer-relevant metrics.
- Document baseline acceptance for MCP tool interactions.

### Day 12 · Deployment & Quick Start
- Review deployment procedures and rollback scripts.
- Ensure health checks and smoke tests are part of review evidence.
- Verify documentation alignment (README, quick start guides).

### Day 15 · Modular Reviewer Rollout
- Evaluate modular reviewer feature flags and operational toggles.
- Cross-check performance metrics against thresholds.
- Highlight regression risk for deprecated tooling.

### Day 17 · Integration Contracts & README
- Confirm integration scenarios pass end-to-end verification.
- Ensure README and contract updates reflect delivered state.
- Coordinate with Analyst on final acceptance summary.

### Days 18-22 · Continuous Assurance
- Track resolution of review findings and regressions.
- Maintain archive-ready review summaries.
- Monitor incident logs for post-release issues.

## Capability Patterns
- **Evidence Matrix**: Map findings to requirements, tests, metrics.
- **Regression Watch**: Flag historical bugs or debt touched by changes.
- **Approval Ledger**: Record approvals with timestamp, reviewer, evidence link.

## Upcoming (Days 23-28) ⏳
- Plan deeper performance audits for reviewer-intensive modules.
- Extend checklists to cover analytics instrumentation.
- Prepare joint review sessions with operations for resilience focus.

## Update Log
- [ ] EP19 – Await developer sign-off
- [ ] EP20 – Prep integration regression suite
- [ ] EP21 – Monitor modular reviewer stabilization reviews
=======
Detailed progression of Reviewer role capabilities through Challenge Days 1-22, focusing on multi-pass review methodology, quality assurance, and automated issue detection.

---

## Day 1 · Basic Code Review
**Capability:** Read code and provide basic feedback
**Use Case:** Review simple function, identify obvious bugs
**Key Technique:** Manual inspection, basic syntax checking
**Status:** ✅ MASTERED (Day 1)

## Day 2 · Structured Feedback
**Capability:** Provide feedback in JSON format with file/line references
**Use Case:** Generate structured review report instead of freeform comments
**Example:**
```json
{
  "file": "src/domain/payment.py",
  "line": 42,
  "severity": "high",
  "issue": "Missing validation for negative amount"
}
```
**Status:** ✅ MASTERED (Day 2)

## Day 3 · Review Stopping Conditions
**Capability:** Know when review is complete (all passes done, all critical issues documented)
**Use Case:** After 3 passes, determine if approved/changes_requested/rejected
**Key Technique:** Checklist-based completion (Architecture + Component + Synthesis)
**Status:** ✅ MASTERED (Day 3)

## Day 4 · Deterministic Review (Temperature=0)
**Capability:** Consistent review results (same code → same findings)
**Use Case:** Run review twice, get identical critical issues list
**Key Technique:** Use T=0.0 for LLM calls, objective metrics (coverage, complexity)
**Status:** ✅ MASTERED (Day 4)

## Day 5 · Model Selection for Review
**Capability:** Use appropriate models for different review passes
**Use Case:** Claude Sonnet 4.5 for architecture pass, GPT-4o-mini for style checks
**Status:** ✅ MASTERED (Day 5)

## Day 6 · Chain of Thought Validation
**Capability:** Use CoT to systematically validate architecture decisions
**Use Case:** "Step-by-step: Does this payment flow handle all error cases?"
**Key Technique:** Break down architecture into components, simulate failure modes
**Example:**
```
CoT Step 1: PaymentService receives request
CoT Step 2: Validate input → What if amount is negative? ✅ Handled
CoT Step 3: Call Stripe API → What if network timeout? ❌ NOT HANDLED
CoT Step 4: Save to DB → What if DB is down? ❌ NOT HANDLED
Result: 2 critical issues found
```
**Status:** ✅ MASTERED (Day 6)

## Day 7 · Multi-Agent Review
**Capability:** Coordinate with other reviewer agents (parallel component reviews)
**Use Case:** Reviewer A reviews architecture, Reviewer B reviews tests simultaneously
**Status:** ✅ MASTERED (Day 7)

## Day 8 · Code Complexity Analysis
**Capability:** Measure and enforce code complexity limits
**Use Case:** Flag functions with cyclomatic complexity >10 or >15 lines
**Key Technique:** Use Radon or similar tool, calculate maintainability index
**Example:**
```python
# Complexity analysis
from radon.complexity import cc_visit

code = open('src/payment.py').read()
complexity = cc_visit(code)
for item in complexity:
    if item.complexity > 10:
        issues.append({
            "severity": "high",
            "message": f"Function {item.name} has complexity {item.complexity} (limit: 10)"
        })
```
**Status:** ✅ MASTERED (Day 8)

## Day 9 · MCP Integration for Review Tools
**Capability:** Query MCP for similar past reviews and common issues
**Use Case:** "Find past reviews of payment modules" → Discover recurring validation bugs
**Status:** ✅ MASTERED (Day 9)

## Day 10 · Custom Review MCP Tools
**Capability:** Create MCP tools for automated checks (architecture validator, test coverage analyzer)
**Use Case:** `validate_clean_architecture(pr)` → Auto-detect layer violations
**Example:**
```python
@mcp.tool()
def validate_clean_architecture(files: list[str]) -> ArchitectureReport:
    """Validate Clean Architecture boundaries."""
    violations = []
    for file in files:
        if 'domain/' in file:
            imports = extract_imports(file)
            if any('infrastructure' in imp for imp in imports):
                violations.append({
                    "file": file,
                    "issue": "Domain imports from Infrastructure (violation)"
                })
    return ArchitectureReport(violations=violations)
```
**Status:** ✅ MASTERED (Day 10)

## Day 11 · Shared Infrastructure Validation
**Capability:** Verify code uses shared MongoDB, Prometheus, logging correctly
**Use Case:** Check if code connects to `mongodb://shared-mongo:27017`, emits metrics to `/metrics`
**Key Technique:** Pattern matching for connection strings, metric definitions
**Status:** ✅ MASTERED (Day 11)

## Day 12 · Deployment Readiness Review
**Capability:** Assess if code is ready for staging/production deployment
**Use Case:** Check for hardcoded secrets, environment variables, health checks
**Key Technique:** Security scan (Bandit), config validation, deployment checklist
**Status:** ✅ MASTERED (Day 12)

## Day 13 · Container & Environment Review
**Capability:** Review Docker configurations, environment setup
**Use Case:** Validate Dockerfile, docker-compose.yml, CI/CD pipeline configs
**Status:** ✅ MASTERED (Day 13)

## Day 14 · Project-Wide Analysis
**Capability:** Review entire codebase for systemic issues (not just PR diff)
**Use Case:** "Find all functions missing error handling" across whole project
**Key Technique:** AST parsing, pattern matching, static analysis
**Status:** ✅ MASTERED (Day 14)

## Day 15 · Review History Compression
**Capability:** Compress past review findings into patterns library
**Use Case:** 50 reviews with "missing input validation" → Pattern: "Always validate user input"
**Key Technique:** Aggregate similar issues, extract common patterns
**Example:**
```python
# Pattern extraction from review history
reviews = db.reviews.find({"epic": {"$gte": "EP15"}})
issue_counts = defaultdict(int)
for review in reviews:
    for issue in review['issues']:
        issue_counts[issue['category']] += 1

# Top patterns
# 1. input_validation: 23 occurrences
# 2. error_handling: 18 occurrences
# 3. test_coverage: 15 occurrences
```
**Status:** ✅ MASTERED (Day 15)

## Day 16 · Review Memory & Learning
**Capability:** Store review findings in external memory (MongoDB) for future reference
**Use Case:** Log all issues found → Future reviews query: "What issues did we find in payment code before?"
**Key Technique:** Structured logging to MongoDB, tagging by domain/component
**Status:** ✅ MASTERED (Day 16)

## Day 17 · Integration Contract Validation
**Capability:** Validate APIs match OpenAPI specs, events match schemas
**Use Case:** "Does PaymentService POST /payments match OpenAPI contract?"
**Key Technique:** Schema validation, contract testing
**Example:**
```python
# Validate API against OpenAPI spec
from openapi_core import create_spec
from openapi_core.validation.request import openapi_request_validator

spec = create_spec(yaml.safe_load(open('api_spec.yaml')))
validator = openapi_request_validator.RequestValidator(spec)
result = validator.validate(request)
if result.errors:
    issues.append({
        "severity": "critical",
        "message": f"API contract violation: {result.errors}"
    })
```
**Status:** ✅ MASTERED (Day 17)

## Day 18 · Production-Grade Review
**Capability:** Focus on production readiness (monitoring, alerting, rollback)
**Use Case:** Check for Prometheus metrics, structured logging, circuit breakers
**Key Technique:** Production checklist validation
**Checklist:**
- [ ] Prometheus metrics exposed
- [ ] Structured logging (JSON format)
- [ ] Error handling with retries
- [ ] Graceful degradation
- [ ] Health check endpoint
- [ ] No hardcoded secrets
**Status:** ✅ MASTERED (Day 18)

## Day 19 · Review Documentation Indexing
**Capability:** Index code and review findings for future RAG retrieval
**Use Case:** Generate embeddings for all review comments → Enable semantic search
**Status:** ✅ MASTERED (Day 19)

## Day 20 · RAG-Powered Review
**Capability:** Query past reviews to find similar issues faster
**Use Case:** Current PR has Stripe adapter → Query: "Past issues with Stripe adapters"
**Key Technique:** Vector search for similar code, retrieve past issues
**Example:**
```javascript
db.reviews.aggregate([
  {
    $vectorSearch: {
      index: "review_vector_index",
      path: "code_embedding",
      queryVector: current_pr_embedding,
      numCandidates: 50,
      limit: 5
    }
  },
  {
    $match: {
      "issues.severity": { $in: ["critical", "high"] },
      "domain": "payment"
    }
  }
]);
// Returns: Top 5 similar past reviews with critical/high issues
```
**Impact:** Review time reduced by 40% (find known issues instantly)
**Status:** ✅ MASTERED (Day 20)

## Day 21 · Issue Prioritization & Ranking
**Capability:** Rank issues by impact (severity + frequency + production risk)
**Use Case:** 10 issues found → Rank: 2 critical (blocking), 5 medium (suggestions), 3 low (defer)
**Key Technique:** Multi-factor scoring
**Formula:**
```python
def calculate_issue_priority(issue: Issue, history: ReviewHistory) -> float:
    """Calculate issue priority score (0-1)."""
    severity_weight = {"critical": 1.0, "high": 0.7, "medium": 0.4, "low": 0.2}
    frequency = history.count_similar_issues(issue) / history.total_reviews
    production_risk = 1.0 if issue.category == "security" else 0.5

    priority = (
        severity_weight[issue.severity] * 0.5 +
        frequency * 0.3 +
        production_risk * 0.2
    )
    return priority
```
**Status:** ✅ MASTERED (Day 21)

## Day 22 · Source Attribution & Citations
**Capability:** Cite sources for review findings (past bugs, MADRs, best practices)
**Use Case:** "Missing error handling → See MADR-067 (retry policy), EP19 had 3 prod bugs from this"
**Impact:** More credible reviews, developers understand "why" not just "what"
**Example:**
```json
{
  "issue": {
    "severity": "high",
    "description": "Missing retry logic for Stripe API calls",
    "citations": [
      {
        "source": "MADR-067",
        "title": "Retry Policy for External APIs",
        "reason": "Architectural decision requires 3 retries with exponential backoff"
      },
      {
        "source": "EP19_bug_report",
        "title": "Production incident: Stripe timeout caused payment loss",
        "reason": "This exact issue caused 12 failed payments in EP19"
      }
    ],
    "suggested_fix": "Add retry decorator from shared.infrastructure.retry_policy"
  }
}
```
**Status:** ✅ MASTERED (Day 22)

---

## Capability Summary Matrix

| Day | Capability | Key Benefit | ROI |
|-----|------------|-------------|-----|
| 6 | Chain of Thought Validation | Systematic architecture review | +35% issue detection |
| 8 | Code Complexity Analysis | Enforce maintainability | Prevent tech debt |
| 10 | Custom Review MCP Tools | Automated checks | -60% manual effort |
| 15 | Review History Compression | Pattern library | Faster reviews |
| 17 | Integration Contract Validation | API correctness | Prevent integration bugs |
| 18 | Production-Grade Review | Production readiness | -90% post-deploy issues |
| 20 | RAG-Powered Review | Find known issues instantly | -40% review time |
| 22 | Source Attribution | Credible feedback | +50% developer buy-in |

---

## Review Efficiency Over Time

### Before RAG & Automation (Days 1-9)
- Review time: 4-6 hours per medium PR
- Issues found: 3-5 per review (mostly obvious)
- False positives: 20% (suggestions marked "won't fix")
- Architecture violations missed: 15%

### After RAG & Automation (Days 10-22)
- Review time: 2-3 hours per medium PR (-50%)
- Issues found: 8-12 per review (including subtle bugs)
- False positives: 5% (-75%)
- Architecture violations missed: 2% (-87%)

**ROI:**
- Review time: -50%
- Issue detection: +160%
- Quality escapes: -87%

---

## Multi-Pass Review Breakdown

### Pass 1: Architecture (30% of time, ~45 min for medium PR)
**Automated:**
- Clean Architecture validator (layer boundaries)
- Dependency analyzer (circular dependencies)
- Integration contract checker

**Manual:**
- Cross-cutting concerns (logging, error handling, metrics)
- MADR compliance
- Design pattern validation

### Pass 2: Component (50% of time, ~75 min)
**Automated:**
- Linter (Flake8, Black)
- Type checker (Mypy)
- Security scanner (Bandit)
- Complexity analyzer (Radon)
- Test coverage (Pytest)

**Manual:**
- Logic correctness
- Edge case handling
- Test quality (not just coverage)
- Code smells (duplication, magic numbers)

### Pass 3: Synthesis (20% of time, ~30 min)
**Automated:**
- Overall quality metrics aggregation
- Production readiness checklist

**Manual:**
- Integration risk assessment
- Deployment considerations
- Final approval decision

---

## Common Issue Patterns (Top 10)

Based on 100+ reviews across EP10-EP23:

1. **Missing Input Validation** (23 occurrences)
   - Severity: High
   - Fix: Add validation in domain layer

2. **Missing Error Handling** (18 occurrences)
   - Severity: Critical
   - Fix: Wrap external calls in try-except

3. **Test Coverage Gaps** (15 occurrences)
   - Severity: Medium
   - Fix: Add tests for edge cases

4. **Architecture Violations** (12 occurrences)
   - Severity: Critical
   - Fix: Move imports to correct layer

5. **Hardcoded Values** (10 occurrences)
   - Severity: Low
   - Fix: Extract to constants or config

6. **Missing Type Hints** (9 occurrences)
   - Severity: Medium
   - Fix: Add type hints (Mypy strict mode)

7. **Complex Functions** (8 occurrences)
   - Severity: Medium
   - Fix: Extract methods, reduce complexity

8. **Missing Docstrings** (7 occurrences)
   - Severity: Low
   - Fix: Add docstrings (Google style)

9. **Security Issues** (5 occurrences)
   - Severity: Critical
   - Fix: Use parameterized queries, encrypt secrets

10. **Poor Naming** (4 occurrences)
    - Severity: Low
    - Fix: Rename for clarity

---

## Linked Resources
- Role Definition: `docs/roles/reviewer/role_definition.md`
- RAG Queries: `docs/roles/reviewer/rag_queries.md`
- Examples: `docs/roles/reviewer/examples/`
- Handoff Contracts: `docs/operational/handoff_contracts.md`
>>>>>>> origin/master
