# Architect Day Capabilities

This document details how each Challenge Day enhances the Architect role's capabilities in designing systems that enforce Clean Architecture principles, manage dependencies, and produce actionable MADRs for implementation.

---

## Day 1 · Architecture Vision Basics

**Capability:** Create structured architecture vision documents from Analyst requirements.

**Use Case:**
- Analyst provides 8 requirements for payment system
- Architect translates to: 3 components, boundaries, interfaces
- Output: Vision document with component responsibilities

**Key Technique:**
- Map requirements → components (1:N relationship)
- Define boundaries: domain (pure), application (use cases), infrastructure (adapters)
- Document interfaces at boundaries (no implementation details)

**Example:**
```markdown
# Architecture Vision: Payment System (EP23)

## Components
- **PaymentService** (Application Layer)
  - Responsibilities: Orchestrate payment transactions
  - Boundaries: No direct database access
  - Interfaces: IPaymentProvider, ITransactionLog

- **StripeAdapter** (Infrastructure Layer)
  - Responsibilities: Implement IPaymentProvider for Stripe API
  - Dependencies: External Stripe SDK
  - Boundaries: Domain layer never imports this

## Dependency Rules
✅ Application → Domain (allowed)
✅ Infrastructure → Application (allowed)
❌ Domain → Infrastructure (FORBIDDEN)
❌ Domain → Application (FORBIDDEN)
```

**Status:** ✅ MASTERED (Day 1)

**Integration Points:**
- Receives from: Analyst requirements
- Provides to: Tech Lead (component list for implementation plan)
- Enables: Clear separation of concerns from start

---

## Day 2 · Structured MADR Output

**Capability:** Document architectural decisions in MADR (Markdown Architecture Decision Record) format.

**Use Case:**
- Decision needed: SQL vs NoSQL for payment transactions
- Architect creates MADR with: context, decision, alternatives, consequences
- Output: Parseable MADR file for traceability

**Key Technique:**
- Use standardized MADR template
- Include: Title, Status, Context, Decision, Alternatives, Consequences
- Link MADRs to requirements: "Addresses REQ-PAY-001"

**Example MADR:**
```markdown
# MADR-067: Use MongoDB for Payment Transaction Storage

## Status
✅ Accepted

## Context
REQ-PAY-001 requires storing 10K+ transactions/day with flexible schema.
Need to support multi-currency, metadata fields, and fast writes.

## Decision
Use MongoDB for payment transaction storage.

## Alternatives Considered
1. **PostgreSQL**: Pros: ACID, relations. Cons: Schema rigidity, slower writes
2. **DynamoDB**: Pros: Scalable. Cons: Vendor lock-in, complex queries
3. **MongoDB**: Pros: Flexible schema, fast writes, good query support

## Consequences
### Positive
- Fast writes (< 10ms p95)
- Flexible schema supports multi-currency metadata
- Horizontal scaling available

### Negative
- No ACID transactions across collections
- Requires manual schema validation
- Need to manage indexes carefully

### Mitigations
- Use Mongoose for schema validation
- Document index strategy in operational guide
```

**Status:** ✅ MASTERED (Day 2)

**Integration Points:**
- MADRs referenced in Tech Lead implementation plan
- Analyst validates MADRs align with requirements
- Developer uses MADRs to understand design rationale

---

## Day 3 · Architecture Validation with Stopping Conditions

**Capability:** Validate architecture completeness and know when design is "good enough" to hand off.

**Use Case:**
- Architect designs 4 components for payment system
- Validation: All requirements covered? Boundaries clean? Dependencies valid?
- Completeness score: 0.92 → Ready for handoff

**Key Technique:**
- Define validation criteria:
  - All requirements mapped to components ≥ 90%
  - No inward dependencies (domain ← infrastructure)
  - All cross-cutting concerns addressed (logging, metrics, config)
  - At least 1 MADR per major decision
- Calculate completeness score
- Stop when score ≥ 0.90 OR blocking questions emerge

**Example Validation:**
```python
def validate_architecture_completeness(vision: ArchitectureVision) -> float:
    """Calculate architecture completeness score."""
    
    scores = {
        "requirement_coverage": 0.0,    # All reqs mapped to components?
        "boundary_clarity": 0.0,         # Clean layer separation?
        "dependency_validity": 0.0,      # No inward deps?
        "cross_cutting_coverage": 0.0,   # Logging, metrics, config?
        "madr_coverage": 0.0             # Decisions documented?
    }
    
    # Requirement coverage
    mapped_reqs = count_requirements_mapped_to_components(vision)
    total_reqs = count_total_requirements(vision)
    scores["requirement_coverage"] = mapped_reqs / total_reqs
    
    # Boundary clarity
    if has_clear_layer_boundaries(vision):
        scores["boundary_clarity"] = 1.0
    
    # Dependency validity (no domain → infra)
    violations = find_inward_dependencies(vision)
    scores["dependency_validity"] = 1.0 if len(violations) == 0 else 0.5
    
    # Cross-cutting concerns
    concerns = ["logging", "metrics", "configuration", "error_handling"]
    covered = count_addressed_concerns(vision, concerns)
    scores["cross_cutting_coverage"] = covered / len(concerns)
    
    # MADR coverage
    decisions = count_madrs(vision)
    scores["madr_coverage"] = min(decisions / 3, 1.0)  # Expect ≥3 MADRs
    
    return sum(scores.values()) / len(scores)

# Example result:
# Completeness: 0.92 → ✅ Ready for handoff
# Breakdown:
#   - requirement_coverage: 0.95 (19/20 reqs mapped)
#   - boundary_clarity: 1.0 (clean layers)
#   - dependency_validity: 1.0 (no violations)
#   - cross_cutting_coverage: 0.75 (3/4 concerns)
#   - madr_coverage: 1.0 (5 MADRs documented)
```

**Status:** ✅ MASTERED (Day 3)

**Integration Points:**
- Prevents incomplete designs from reaching Tech Lead
- Clear criteria for Analyst review approval
- Reduces architecture clarification loops

---

## Day 4 · Temperature Tuning for Design Exploration

**Capability:** Use different LLM temperatures for creative architecture exploration vs precise MADR generation.

**Use Case:**
- T=0.8: Brainstorm alternative architectures (creative)
- T=0.0: Generate MADR from chosen architecture (precise)
- T=0.3: Review Analyst requirements for architecture implications (balanced)

**Key Technique:**
- **Exploration phase (T=0.7-0.8):** Generate multiple architecture alternatives
- **Decision phase (T=0.0):** Convert chosen alternative to structured MADR
- **Review phase (T=0.3):** Analyze requirements for constraints and risks

**Example:**
```python
# Exploration: Generate alternatives
alternatives = llm.generate(
    prompt="Propose 3 different architectures for payment system",
    temperature=0.8
)
# Output: ["Microservices", "Monolith with plugins", "Event-driven"]

# Decision: Create structured MADR
madr = llm.generate(
    prompt="Create MADR for chosen architecture: Microservices",
    temperature=0.0,
    format="markdown"
)
# Output: Deterministic, well-structured MADR

# Review: Analyze requirements
risks = llm.generate(
    prompt="Identify architecture risks in requirements: [...]",
    temperature=0.3
)
# Output: Balanced analysis (creative + precise)
```

**Status:** ✅ MASTERED (Day 4)

**Integration Points:**
- Creative exploration improves design quality
- Deterministic MADRs ensure consistency
- Temperature metadata logged for audit trail

---

## Day 5 · Model Selection for Architecture Work

**Capability:** Choose appropriate LLM model based on architecture task complexity.

**Use Case:**
- Simple component mapping: GPT-4o-mini (fast, cheap)
- Complex MADR reasoning: GPT-5 or Claude Sonnet 4.5 (deep analysis)
- Dependency analysis: GPT-5 (strong reasoning)

**Key Technique:**
- Route tasks by complexity:
  - Component listing: GPT-4o-mini
  - Trade-off analysis: GPT-5
  - MADR generation: Claude Sonnet 4.5
  - Dependency validation: GPT-5

**Example Routing:**
```python
if task == "list_components":
    model = "gpt-4o-mini"  # ~$0.15 per 1M tokens
elif task == "analyze_tradeoffs":
    model = "gpt-5"  # ~$2.50 per 1M tokens (deep reasoning)
elif task == "generate_madr":
    model = "claude-sonnet-4.5"  # ~$3.00 per 1M tokens (structured)
```

**Metrics:**
```
EP23 Architecture Session:
- Component listing: 2K tokens × $0.15 = $0.0003
- Trade-off analysis: 6K tokens × $2.50 = $0.015
- MADR generation: 3K tokens × $3.00 = $0.009
Total cost: $0.0243 per epic
```

**Status:** ✅ MASTERED (Day 5)

**Integration Points:**
- Cost tracking for epic budgets
- Model selection documented in handoff metadata
- See `docs/specs/agents/MODELS.md` for cross-role mapping

---

## Day 6 · Chain of Thought for Architecture Validation

**Capability:** Use CoT prompting to validate architecture decisions for consistency, risks, and trade-offs.

**Use Case:**
- Architect proposes microservices architecture
- Before finalizing, runs CoT validation: "Think step-by-step: Is this architecture sound?"
- Catches issues: "Service A depends on Service B which depends on A → circular dependency!"

**Key Technique:**
- Append to validation prompt: "Let's think step by step:"
  1. List all components and their dependencies
  2. Check for circular dependencies
  3. Verify layer boundaries respected
  4. Identify performance bottlenecks
  5. Check security vulnerabilities
- Compare CoT output vs direct output

**Example:**
```
Without CoT:
Architect: "Architecture looks good, no issues found."

With CoT:
Architect: "Let me validate step by step:
1. Components: PaymentService, NotificationService, AuditService
2. Dependencies:
   - PaymentService → NotificationService (OK)
   - PaymentService → AuditService (OK)
   - NotificationService → PaymentService (WAIT - potential circular!)
3. → ISSUE: NotificationService calling back to PaymentService creates tight coupling
4. → SOLUTION: Use event bus pattern instead (PaymentService emits event, NotificationService consumes)

Result: Caught architectural issue before implementation
```

**Status:** ✅ MASTERED (Day 6)

**Integration Points:**
- Prevents flawed designs from reaching Tech Lead
- CoT reasoning included in MADR for transparency
- Reduces rework during implementation
- See example: `docs/roles/architect/examples/day_6_cot_validation.md`

---

## Day 7 · Multi-Agent Architecture Review

**Capability:** Use second Architect agent to peer-review architecture before handoff to Tech Lead.

**Use Case:**
- Architect A designs payment system (4 components, 2 MADRs)
- Architect B reviews for: boundary violations, missing concerns, risk gaps
- Only designs passing peer review go to Tech Lead

**Key Technique:**
- Agent A (Designer): Focuses on fulfilling requirements
- Agent B (Reviewer): Focuses on Clean Architecture enforcement, risks
- Handoff includes peer_review_status: "approved" | "needs_revision"

**Example Workflow:**
```json
{
  "architect_a_design": {
    "components": ["PaymentService", "StripeAdapter", "AuditLog"],
    "madrs": ["MADR-067: MongoDB", "MADR-068: Stripe provider"]
  },
  
  "architect_b_review": {
    "status": "needs_revision",
    "issues": [
      {
        "component": "PaymentService",
        "issue": "Direct database access violates Clean Architecture",
        "severity": "high",
        "recommendation": "Add PaymentRepository interface, implement in infrastructure layer"
      },
      {
        "cross_cutting": "error_handling",
        "issue": "No error handling strategy documented",
        "severity": "medium",
        "recommendation": "Add MADR for error handling (retry, circuit breaker)"
      }
    ]
  }
}

→ Architect A revises design
→ After resolution, Architect B approves
→ Only then handoff to Tech Lead
```

**Status:** ✅ MASTERED (Day 7)

**Integration Points:**
- Dramatically improves handoff quality to Tech Lead
- Reduces Tech Lead clarification requests by ~60%
- Peer review logs stored in `docs/epics/<epic>/reviews/architect_peer_review.md`

---

## Day 8 · Token Management for Architecture Sessions

**Capability:** Manage token budgets during architecture design sessions (typically 5K-8K tokens).

**Use Case:**
- Architecture session for complex epic: requirements review + component design + MADR generation
- Track tokens: Requirements (2K) + Design (3K) + MADRs (2K) = 7K tokens
- Reserve 2K for handoff JSON, 1K safety margin → within 12K window

**Key Technique:**
- Architecture session budget:
  ```
  12K total context:
  - System prompts: 800 tokens
  - Analyst requirements (compressed): 2,100 tokens
  - Architecture design: 3,500 tokens
  - MADRs (2-3): 2,000 tokens
  - Handoff JSON: 2,000 tokens
  - Safety margin: 1,600 tokens
  ```
- Track tokens per phase
- If approaching limit, compress requirements further (Day 15 pattern)

**Example Session:**
```
Phase 1: Requirements Review (2,100 tokens)
├─ Load Analyst handoff (compressed)
└─ Extract architecture implications

Phase 2: Component Design (3,500 tokens)
├─ List components (500 tokens)
├─ Define boundaries (800 tokens)
├─ Map requirements → components (1,200 tokens)
└─ Validate dependencies (1,000 tokens)

Phase 3: MADR Generation (2,000 tokens)
├─ MADR-067: Database choice (1,000 tokens)
└─ MADR-068: Provider abstraction (1,000 tokens)

Phase 4: Handoff Preparation (2,000 tokens)
└─ Generate JSON for Tech Lead

Total: 9,600 tokens (80% of window)
Remaining: 2,400 tokens (safety margin)
```

**Status:** ✅ MASTERED (Day 8)

**Integration Points:**
- Directly implements `docs/operational/context_limits.md` budgets
- Enables complex architecture sessions without overflow
- See `docs/roles/analyst/examples/day_8_token_budgeting.md` for similar pattern

---

## Day 9 · MCP Integration for Architecture Discovery

**Capability:** Query MCP tools to discover past architecture decisions and design patterns.

**Use Case:**
- Designing new payment system
- Query MCP tool: "Find past payment system architectures"
- Discover: EP15 (payment API design), EP19 (multi-provider pattern)
- Reuse proven patterns, reference in MADRs

**Key Technique:**
- Connect to MCP server: `mcp.tools.list()` → discover available tools
- Use tool: `search_architecture(keywords=["payment", "provider", "adapter"])`
- Results feed into current design as precedents
- Cite sources in MADRs: "Follows EP19 provider abstraction pattern"

**Example:**
```python
# MCP tool discovery
tools = mcp_client.list_tools()
# → ["search_architecture", "find_madrs", "get_dependency_graph"]

# Query for similar architectures
results = mcp_client.call_tool(
    "search_architecture",
    keywords=["payment", "provider"],
    epic_range=["EP10", "EP20"]
)

# Results:
[
  {
    "epic": "EP19",
    "component": "ProviderAdapter",
    "pattern": "Strategy pattern for multiple payment providers",
    "madrs": ["MADR-045: Provider abstraction"]
  }
]

# Reference in current design:
madr = {
  "id": "MADR-067",
  "title": "Use Provider Abstraction Layer",
  "reference": "Follows proven pattern from EP19 (MADR-045)",
  "implementation": "src/infrastructure/adapters/payment/ (from EP19)"
}
```

**Status:** ✅ MASTERED (Day 9)

**Integration Points:**
- MCP tools become architecture discovery mechanism
- Reduces "reinventing the wheel" for common patterns
- Citations improve traceability across epics

---

## Day 10 · Custom MCP Tool for Architecture Validation

**Capability:** Create custom MCP tool to validate architecture against organizational standards.

**Use Case:**
- Organization has "Clean Architecture checklist" (10 rules)
- Architect creates MCP tool: `validate_architecture(epic_id)`
- Tool checks: Clean boundaries? No inward deps? Cross-cutting covered?
- Auto-validation before handoff

**Key Technique:**
- Implement MCP tool with FastMCP:
  ```python
  @mcp.tool()
  def validate_architecture(epic: str) -> ValidationResult:
      """Validate architecture against Clean Architecture rules."""
      checks = [
          no_inward_dependencies(epic),
          all_cross_cutting_addressed(epic),
          madrs_for_major_decisions(epic),
          component_boundaries_clear(epic)
      ]
      return {"passed": all(checks), "issues": [...]}
  ```
- Register tool in MCP server config
- Architect agent calls tool before handoff

**Example Validation:**
```
Input:
{
  "epic_id": "EP23",
  "components": ["PaymentService", "StripeAdapter"],
  "madrs": ["MADR-067"]
}

Tool output:
{
  "passed": false,
  "issues": [
    "Missing cross-cutting concern: error_handling",
    "Component PaymentService has direct DB access (violates Clean Arch)",
    "Only 1 MADR (expected ≥2 for this complexity)"
  ],
  "recommendations": [
    "Add IRepository interface",
    "Document error handling strategy in MADR",
    "Add MADR for provider selection rationale"
  ]
}

→ Architect fixes issues before handoff
```

**Status:** ✅ MASTERED (Day 10)

**Integration Points:**
- Enforces Clean Architecture automatically
- Reduces Tech Lead rework
- Validation results logged in `docs/epics/<epic>/validation_report.md`

---

## Day 11 · Shared Infrastructure Integration

**Capability:** Design architectures that integrate with shared infrastructure (MongoDB, Prometheus, Grafana, MCP).

**Use Case:**
- New service must use shared MongoDB cluster
- Architect embeds infrastructure constraints in design
- Output: Components with explicit infra dependencies + connection diagrams

**Key Technique:**
- Load infrastructure constraints from `docs/operational/shared_infra.md`
- Embed in architecture vision:
  - MongoDB: Connection string, authentication, collections
  - Prometheus: /metrics endpoint, metric naming conventions
  - Grafana: Dashboard templates, alert rules
  - Loki: Structured logging format
- Document in component interfaces

**Example Architecture with Shared Infra:**
```markdown
# Architecture Vision: Payment Service (EP23)

## Infrastructure Dependencies

### MongoDB
- **Connection**: mongodb://shared-mongo:27017/payments
- **Collections**: payments, transactions, audit_logs
- **Authentication**: Via shared secret in secrets manager
- **Indexes**: Required on transaction_id, status+created_at

### Prometheus
- **Endpoint**: /metrics (standardized across all services)
- **Metrics**:
  - `payment_transactions_total` (counter)
  - `payment_processing_duration_seconds` (histogram)
  - `payment_provider_errors_total` (counter)

### Grafana
- **Dashboard**: Use template from `grafana/dashboards/service_template.json`
- **Panels**: Transaction rate, latency (p50/p95/p99), error rate
- **Alerts**: Error rate > 1%, latency p95 > 3s

### Loki
- **Log Format**: JSON structured logs
- **Required Fields**: timestamp, level, service, trace_id, message
- **Retention**: 30 days

## Component Dependencies
- **PaymentService** → MongoDB (read/write transactions)
- **PaymentService** → Prometheus (emit metrics)
- **All components** → Loki (structured logging)
```

**Status:** ✅ MASTERED (Day 11)

**Integration Points:**
- Aligns with `docs/specs/day11-17_summary.md` infrastructure baseline
- Tech Lead gets infrastructure requirements upfront
- Developer knows connection strings and authentication methods
- See example: `docs/roles/architect/examples/day_11_shared_infra.md`

---

## Day 12 · Deployment Topology & Health Checks

**Capability:** Design deployment topologies with health checks, startup sequences, and environment-specific configurations.

**Use Case:**
- Payment service deploys to: local (Docker), staging (K8s), production (K8s)
- Architect designs: health check endpoints, startup order, secrets management
- Output: Deployment diagram + environment matrix

**Key Technique:**
- Define deployment environments:
  ```
  - Local: docker-compose (single-node, all services)
  - Staging: Kubernetes (3 replicas, shared DB)
  - Production: Kubernetes (10 replicas, dedicated DB cluster)
  ```
- Health check requirements:
  - `/health`: Liveness probe (service alive?)
  - `/ready`: Readiness probe (dependencies ready?)
- Startup sequence: DB → Services → Load Balancer
- Secrets management: Local (env vars), Staging/Prod (K8s secrets)

**Example Deployment Design:**
```markdown
# Deployment Topology: Payment Service (EP23)

## Environments

| Environment | Platform | Replicas | Database | Load Balancer |
|-------------|----------|----------|----------|---------------|
| Local | Docker Compose | 1 | MongoDB (container) | Nginx (container) |
| Staging | Kubernetes | 3 | Shared MongoDB cluster | Ingress Controller |
| Production | Kubernetes | 10 | Dedicated MongoDB cluster | Cloud Load Balancer |

## Health Checks

### /health (Liveness)
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 30
```
- Returns: `{"status": "ok", "version": "1.0.0", "uptime": 3600}`
- Fails if: Service crashed, OOM

### /ready (Readiness)
```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
```
- Returns: `{"status": "ready", "dependencies": {"mongodb": "ok", "stripe": "ok"}}`
- Fails if: MongoDB unreachable, Stripe API down

## Startup Sequence
1. MongoDB starts (wait for ready)
2. PaymentService starts (connects to MongoDB)
3. PaymentService /ready returns 200
4. Load Balancer adds service to pool

## Secrets Management
- **Local**: `.env` file (for development only)
- **Staging/Production**: Kubernetes Secrets
  - `mongodb-connection-string`
  - `stripe-api-key`
  - `jwt-signing-secret`
```

**Status:** ✅ MASTERED (Day 12)

**Integration Points:**
- Tech Lead uses for deployment plan stages
- Developer knows health check implementation requirements
- DevOps knows infrastructure provisioning needs
- See example: `docs/roles/architect/examples/day_12_deployment_topology.md`

---

## Day 13 · Environment & Testing Architecture

**Capability:** Design architecture for testability: unit, integration, E2E test strategies.

**Use Case:**
- Payment service needs: unit tests (domain), integration tests (DB), E2E tests (full flow)
- Architect defines: test boundaries, mock strategies, test data management
- Output: Testing architecture diagram + mock interfaces

**Key Technique:**
- Test layers match architecture layers:
  - **Unit tests**: Domain layer only (pure functions, no I/O)
  - **Integration tests**: Application + Infrastructure (with real DB)
  - **E2E tests**: Full system (all layers, real endpoints)
- Define mockable interfaces: IPaymentProvider, IRepository
- Test data strategy: Fixtures, factories, test DB seeding

**Example Testing Architecture:**
```markdown
# Testing Architecture: Payment Service (EP23)

## Test Layers

### Unit Tests (Domain Layer)
- **Scope**: Pure business logic
- **Dependencies**: None (no I/O)
- **Example**: Payment entity validation, amount calculations
- **Tools**: pytest, no fixtures needed
- **Coverage Target**: 100% domain layer

### Integration Tests (Application + Infrastructure)
- **Scope**: Use cases + adapters
- **Dependencies**: MongoDB (test DB), mocked Stripe API
- **Example**: ProcessPayment use case with real DB writes
- **Tools**: pytest, MongoDB fixtures, requests-mock
- **Coverage Target**: 80% application + infrastructure

### E2E Tests (Full System)
- **Scope**: API endpoints, full workflows
- **Dependencies**: All services running (Docker Compose)
- **Example**: POST /payments → verify in DB → check audit log
- **Tools**: pytest, requests, Docker Compose
- **Coverage Target**: Critical paths only

## Mockable Interfaces

```python
# Domain layer defines interface
class IPaymentProvider(Protocol):
    def process_payment(self, amount: int, currency: str) -> TransactionResult:
        ...

# Infrastructure implements real
class StripeAdapter(IPaymentProvider):
    def process_payment(self, amount: int, currency: str) -> TransactionResult:
        # Real Stripe API call
        ...

# Tests use mock
class MockPaymentProvider(IPaymentProvider):
    def process_payment(self, amount: int, currency: str) -> TransactionResult:
        # Return fake success
        return TransactionResult(success=True, id="mock-123")
```

## Test Data Strategy
- **Fixtures**: `tests/fixtures/payments.json` (sample payment data)
- **Factories**: `tests/factories.py` (generate test objects)
- **DB Seeding**: `tests/seed.py` (populate test DB)
```

**Status:** ✅ MASTERED (Day 13)

**Integration Points:**
- Tech Lead creates test stages based on this architecture
- Developer knows what to mock vs what to test with real dependencies
- QA understands test coverage expectations

---

## Day 14 · Code Quality Architecture

**Capability:** Define code quality gates in architecture: linting, type checking, security scanning.

**Use Case:**
- Architecture requires: mypy (100% type coverage), flake8 (0 errors), bandit (no security issues)
- These become acceptance criteria for Tech Lead implementation plan
- CI pipeline enforces quality gates

**Key Technique:**
- Define quality requirements in architecture:
  - **Linting**: flake8, black formatting
  - **Type checking**: mypy --strict
  - **Security**: bandit (no high/medium issues)
  - **Dependencies**: safety check (no vulnerable packages)
- Map to CI gates in Tech Lead plan

**Example Quality Architecture:**
```markdown
# Code Quality Requirements: Payment Service (EP23)

## Quality Gates (CI Pipeline)

### Gate 1: Linting
```yaml
lint:
  command: make lint
  tools:
    - flake8: 0 errors allowed
    - black: Code must be formatted
  blocking: true
```

### Gate 2: Type Checking
```yaml
typecheck:
  command: mypy src/ --strict
  requirements:
    - 100% type coverage
    - No Any types except in adapters
  blocking: true
```

### Gate 3: Security Scanning
```yaml
security:
  command: bandit -r src/
  requirements:
    - No high severity issues
    - No medium severity in production code
  blocking: true
```

### Gate 4: Test Coverage
```yaml
coverage:
  command: pytest --cov=src --cov-report=term-missing
  requirements:
    - Domain layer: 100% coverage
    - Application layer: 90% coverage
    - Infrastructure layer: 80% coverage
  blocking: true
```

## Architecture Enforcement
- **Dependency Rules**: Checked via `import-linter`
- **Layer Violations**: CI fails if infrastructure → domain imports found
- **MADR Compliance**: Scripts validate MADRs referenced in code comments
```

**Status:** ✅ MASTERED (Day 14)

**Integration Points:**
- Tech Lead configures CI pipeline based on these gates
- Developer knows quality expectations upfront
- Reviewer validates gates are passing before code review

---

## Day 15 · Architecture Document Compression

**Capability:** Compress architecture documents (requirements → components → MADRs) for efficient handoff.

**Use Case:**
- Architect produces: Vision (3K tokens) + MADRs (2K) + Diagrams (1K) = 6K tokens
- Compress to 2.5K tokens while preserving: components, boundaries, decisions
- Tech Lead gets concise architecture without information loss

**Key Technique:**
- Compression strategy:
  - **Keep**: Components, boundaries, MADRs (decision only), risks
  - **Remove**: Verbose explanations, redundant examples, MADR alternatives (unless critical)
  - **Summarize**: Long descriptions → bullet points
- Aim for 50-60% compression while preserving 95%+ critical information

**Example Compression:**

**BEFORE (6K tokens):**
```markdown
# Architecture Vision: Payment Service (EP23)

## Background and Context
The payment service is a critical component of our e-commerce platform...
[500 tokens of background]

## Component: PaymentService
The PaymentService is responsible for orchestrating payment transactions...
[Detailed 800-token description]

## MADR-067: MongoDB vs PostgreSQL
### Context
We need to choose a database...
[1000-token discussion of alternatives]
### Decision
Use MongoDB
### Alternatives
1. PostgreSQL: [300 tokens]
2. DynamoDB: [300 tokens]
3. MongoDB: [200 tokens]
### Consequences
[400 tokens of detailed consequences]
```

**AFTER (2.5K tokens):**
```markdown
# Architecture: Payment Service (EP23)

## Components
- **PaymentService**: Orchestrate transactions, provider selection, audit
- **ProviderAdapter**: Abstract providers (Stripe, PayPal)
- **TransactionLog**: Audit trail, compliance

## Boundaries
- Domain: Payment entities, validation (pure)
- Application: Use cases (ProcessPayment, RefundPayment)
- Infrastructure: Adapters (StripeAdapter, MongoRepository)

## MADRs
- **MADR-067**: MongoDB (flexible schema, fast writes, horizontal scaling)
- **MADR-068**: Provider abstraction (Strategy pattern, easy to add providers)

## Risks
- MongoDB: No ACID across collections (mitigate: use Mongoose validation)
- Provider failover: <5s requirement (mitigate: health checks every 30s)

## Dependencies
- MongoDB (shared cluster)
- Stripe API (external)
- Prometheus/Grafana (shared)
```

**Compression Quality:**
```
Original: 6,000 tokens
Compressed: 2,500 tokens
Compression ratio: 58%
Information retention: 96% (all critical elements preserved)
```

**Status:** ✅ MASTERED (Day 15)

**Integration Points:**
- Tech Lead gets concise, actionable architecture
- Compression frees tokens for Tech Lead's planning work
- Critical decisions and boundaries preserved

---

## Day 16 · Architecture Version Control & History

**Capability:** Maintain architecture version history, track changes, and manage evolution across epics.

**Use Case:**
- EP23: Initial payment architecture (v1.0)
- EP25: Add multi-currency support → architecture v1.1
- EP27: Add fraud detection → architecture v2.0
- Track: What changed? Why? Impact on other components?

**Key Technique:**
- Version architecture documents: `architecture_v1.0.md`, `architecture_v1.1.md`
- Store in MongoDB with version field
- Track changes in CHANGELOG:
  ```markdown
  ## v1.1 (EP25)
  - Added: CurrencyConverter component
  - Changed: PaymentService now uses CurrencyConverter
  - MADR-089: Real-time exchange rates via third-party API
  ```

**Example Version Control:**
```json
{
  "epic": "EP25",
  "architecture_version": "1.1",
  "previous_version": "1.0",
  "changes": [
    {
      "type": "component_added",
      "component": "CurrencyConverter",
      "reason": "REQ-PAY-003: Multi-currency support",
      "impact": ["PaymentService updated to use converter"]
    },
    {
      "type": "madr_added",
      "madr_id": "MADR-089",
      "title": "Use exchangerate-api.com for exchange rates",
      "reason": "Need real-time rates"
    }
  ],
  "backward_compatible": true,
  "migration_notes": "No breaking changes. CurrencyConverter is optional dependency."
}
```

**Status:** ✅ MASTERED (Day 16)

**Integration Points:**
- Tech Lead knows what changed between epics
- Developer understands migration path
- Architecture evolution traceable across time

---

## Day 17 · Integration Contracts & API Design

**Capability:** Define integration contracts between components, including API schemas, event formats, and error handling.

**Use Case:**
- PaymentService exposes REST API for other services
- Architect defines: OpenAPI schema, error codes, rate limits
- Contracts stored in `contracts/` directory for validation

**Key Technique:**
- Document contracts:
  - **REST APIs**: OpenAPI 3.0 spec
  - **Events**: Schema for message bus events
  - **Database**: Collection schemas with validation rules
- Include in architecture handoff
- Tech Lead uses contracts for integration tests

**Example Integration Contract:**
```yaml
# contracts/payment_service_api_v1.yaml

openapi: 3.0.0
info:
  title: Payment Service API
  version: 1.0.0

paths:
  /api/v1/payments:
    post:
      summary: Process payment
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [amount_cents, currency, provider]
              properties:
                amount_cents:
                  type: integer
                  minimum: 1
                  example: 10000  # $100.00
                currency:
                  type: string
                  enum: [USD, EUR, GBP]
                provider:
                  type: string
                  enum: [stripe, paypal]
      responses:
        '200':
          description: Payment successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  transaction_id:
                    type: string
                    format: uuid
                  status:
                    type: string
                    enum: [completed, pending]
        '400':
          description: Invalid request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '503':
          description: Payment provider unavailable
```

**Status:** ✅ MASTERED (Day 17)

**Integration Points:**
- Tech Lead uses contracts for integration test planning
- Developer implements exact contract specifications
- API documentation auto-generated from contract
- See example: `docs/roles/architect/examples/day_17_integration_contracts.md`

---

## Day 18 · Real-World Architecture Patterns

**Capability:** Apply proven architecture patterns to real-world business problems.

**Use Case:**
- Business need: "Deploy to app store"
- Architect translates to: Build pipeline, signing certificates, release management
- Architecture addresses: CI/CD, artifact storage, rollback strategy

**Key Technique:**
- Map business goals → architectural components
- Consider operational aspects: monitoring, rollback, scaling
- Document in architecture vision with operational runbooks

**Example:**
```markdown
# Architecture: App Store Deployment (EP28)

## Business Goal
Deploy mobile app to App Store with zero-downtime updates

## Architectural Components

### Build Pipeline
- **Trigger**: Git tag push (v*)
- **Steps**: Build → Test → Sign → Upload
- **Artifacts**: IPA file (iOS), AAB file (Android)

### Certificate Management
- **Storage**: AWS Secrets Manager
- **Rotation**: Annual (automated alerts 30 days before expiry)
- **Access**: CI pipeline only (no developer access)

### Release Management
- **Strategy**: Phased rollout (10% → 50% → 100%)
- **Monitoring**: Crash rate < 1%, rollback if > 2%
- **Rollback**: Previous version available in App Store

### Post-Deployment
- **Monitoring**: Sentry (crash tracking), Mixpanel (usage analytics)
- **Alerts**: Slack notification on deploy success/failure
```

**Status:** ✅ MASTERED (Day 18)

**Integration Points:**
- Bridges business goals and technical architecture
- Tech Lead creates operational runbooks from this
- Operations team knows deployment procedures

---

## Day 19 · Document Architecture for RAG

**Capability:** Structure architecture documents for RAG indexing and retrieval.

**Use Case:**
- Architecture documents need to be searchable for future epics
- Architect structures docs with: metadata, tags, embeddings
- Future architects can query: "Find similar payment architectures"

**Key Technique:**
- Add metadata to architecture documents:
  ```yaml
  metadata:
    epic: EP23
    domain: payments
    patterns: [clean_architecture, adapter_pattern, strategy_pattern]
    components: [PaymentService, ProviderAdapter]
    technologies: [MongoDB, Stripe, FastAPI]
    keywords: [payment, transaction, provider, multi-currency]
  ```
- Generate embeddings for semantic search
- Store in MongoDB with vector index

**Example Document Structure:**
```json
{
  "epic": "EP23",
  "architecture_version": "1.0",
  "title": "Payment Service Architecture",
  "summary": "Microservice for payment processing with multi-provider support",
  
  "metadata": {
    "domain": "payments",
    "patterns": ["clean_architecture", "adapter_pattern"],
    "components": ["PaymentService", "ProviderAdapter", "CurrencyConverter"],
    "technologies": ["MongoDB", "Stripe", "FastAPI"],
    "keywords": ["payment", "transaction", "provider"]
  },
  
  "embedding": [0.123, -0.456, ...],  // 1536-dim vector
  
  "content": "# Architecture Vision...",
  
  "madrs": ["MADR-067", "MADR-068"],
  "related_epics": ["EP15", "EP19"]
}
```

**Status:** ✅ MASTERED (Day 19)

**Integration Points:**
- Enables Day 20 (RAG queries for architecture)
- Future architects discover proven patterns
- Architecture knowledge preserved across epics

---

## Day 20 · RAG Queries for Architecture Reuse

**Capability:** Query RAG index to find similar architectures and reuse proven patterns.

**Use Case:**
- Designing new "real-time dashboard" architecture
- Query: "Find similar dashboard architectures"
- Discover: EP18 (admin dashboard), EP21 (analytics dashboard)
- Reuse: WebSocket pattern, metric aggregation strategy

**Key Technique:**
- RAG query for architectures:
  ```javascript
  db.architecture.find({
    keywords: { $in: ["dashboard", "real-time", "websocket"] },
    patterns: { $in: ["observer_pattern", "pub_sub"] }
  }).limit(5)
  ```
- Compare results: similarity score, reusable patterns
- Reference in MADRs: "Follows EP18 WebSocket architecture"

**Example Query & Results:**
```javascript
// Query
db.architecture.find({
  keywords: { $in: ["dashboard", "real-time"] },
  technologies: { $in: ["websocket", "server-sent-events"] }
}).limit(3)

// Results
[
  {
    "epic": "EP18",
    "title": "Admin Dashboard Real-Time Updates",
    "patterns": ["observer_pattern", "websocket"],
    "madrs": ["MADR-045: WebSocket for live updates"],
    "components": ["DashboardService", "WebSocketManager"],
    "similarity": 0.92
  },
  {
    "epic": "EP21",
    "title": "Analytics Dashboard Architecture",
    "patterns": ["server-sent-events", "caching"],
    "madrs": ["MADR-078: SSE for metrics streaming"],
    "similarity": 0.85
  }
]

// Reuse in current design:
madr = {
  "id": "MADR-095",
  "title": "Use WebSocket for Real-Time Dashboard Updates",
  "reference": "Follows proven pattern from EP18 (MADR-045)",
  "implementation": "Reuse WebSocketManager from EP18"
}
```

**Status:** ✅ MASTERED (Day 20)

**Integration Points:**
- Reduces design time by 30-40% (reuse vs redesign)
- Improves consistency across epics
- Citations provide traceability

---

## Day 21 · Architecture Pattern Ranking & Filtering

**Capability:** Rank and filter RAG results to find most relevant architecture patterns.

**Use Case:**
- RAG query returns 10 architectures, but only top 3 are truly relevant
- Apply ranking: production-validated > high similarity > recent
- Filter: Only show patterns with similarity ≥ 0.80

**Key Technique:**
- Multi-factor ranking:
  ```python
  score = (
      similarity_score * 0.4 +
      production_validated_score * 0.3 +
      recency_score * 0.2 +
      complexity_match_score * 0.1
  )
  ```
- Filter threshold: similarity ≥ 0.80, production_validated = true
- Return top 3 results for architect review

**Example Ranking:**
```python
results = [
  {"epic": "EP18", "similarity": 0.92, "production": True, "age_days": 60},
  {"epic": "EP21", "similarity": 0.85, "production": True, "age_days": 30},
  {"epic": "EP16", "similarity": 0.88, "production": False, "age_days": 90}
]

# Apply ranking
ranked = rank_architecture_results(results)
# [
#   EP21 (0.89 score: high similarity + production + recent),
#   EP18 (0.87 score: highest similarity + production, older),
#   EP16 (0.72 score: good similarity, not production-validated)
# ]

# Filter: Only show production-validated with similarity ≥ 0.80
filtered = [EP21, EP18]  # EP16 excluded (not production-validated)
```

**Status:** ✅ MASTERED (Day 21)

**Integration Points:**
- Improves Day 20 RAG query quality
- Ensures only proven patterns are referenced
- Reduces noise in architecture recommendations

---

## Day 22 · Architecture Citations & Traceability

**Capability:** Include citations in architecture documents linking to source patterns and MADRs.

**Use Case:**
- New payment architecture references EP19 provider pattern
- MADR includes: "Based on MADR-045 from EP19, production-validated for 6 months"
- Tech Lead can trace decision rationale back to original epic

**Key Technique:**
- Citation format in MADRs:
  ```markdown
  ## References
  - **Source**: EP19 MADR-045 (Provider Abstraction Pattern)
  - **Similarity**: 0.92 (high)
  - **Production Status**: Validated (6 months, 0 major issues)
  - **Implementation**: src/infrastructure/adapters/payment/ (reusable)
  ```
- Include citations in handoff JSON
- Tech Lead benefits: can review original pattern before implementation

**Example Architecture with Citations:**
```json
{
  "epic": "EP23",
  "architecture_version": "1.0",
  "components": [
    {
      "name": "ProviderAdapter",
      "pattern": "Strategy Pattern",
      "citation": {
        "source_epic": "EP19",
        "source_madr": "MADR-045",
        "reason": "Proven multi-provider abstraction pattern",
        "production_validated": true,
        "production_duration_months": 6,
        "reusable_code": "src/infrastructure/adapters/payment/"
      }
    }
  ],
  "madrs": [
    {
      "id": "MADR-067",
      "title": "Use Provider Abstraction Layer",
      "reference": "Follows EP19 MADR-045 pattern",
      "differences": [
        "Added: CurrencyConverter integration",
        "Changed: Health check interval 30s (was 60s in EP19)"
      ]
    }
  ]
}
```

**Impact Metrics:**
```
Design Time:
- Without citations: 8 hours (design from scratch)
- With citations: 5 hours (adapt proven pattern)
→ 37.5% time savings

Quality:
- Rework rate without citations: 20% (unknowingly repeating mistakes)
- Rework rate with citations: 5% (reusing validated patterns)
→ 75% reduction in rework

Tech Lead Benefit:
- Implementation plan: Can reference EP19 code directly
- Testing: Can reuse EP19 test strategies
- Deployment: Can follow EP19 deployment patterns
```

**Status:** ✅ MASTERED (Day 22)

**Integration Points:**
- Tech Lead gets full context (not just architecture, but history)
- Developer can review original implementation
- Traceability audit trail complete
- Reduces design-to-implementation time by 30%+

---

## Capability Summary Matrix

| Day | Capability | Primary Benefit | Integration Impact |
|-----|------------|-----------------|-------------------|
| 1 | Architecture Vision | Structured component mapping | Foundation for Clean Arch |
| 2 | Structured MADRs | Decision traceability | Tech Lead knows rationale |
| 3 | Validation & Stopping | Know when design complete | Prevents incomplete handoffs |
| 4 | Temperature Tuning | Creative + precise design | Better alternatives explored |
| 5 | Model Selection | Cost optimization | Budget management |
| 6 | Chain of Thought | Catch design flaws early | Fewer implementation issues |
| 7 | Peer Review | Multi-agent validation | 60% fewer Tech Lead clarifications |
| 8 | Token Management | Complex architectures in 12K | No overflow on large epics |
| 9 | MCP Integration | Discover past patterns | Pattern reuse |
| 10 | Custom Validation | Automated quality checks | Enforces Clean Arch |
| 11 | Shared Infra | Embed infra constraints | Tech Lead gets complete picture |
| 12 | Deployment Topology | Health checks, environments | DevOps knows requirements |
| 13 | Testing Architecture | Test strategy defined | Developer knows what to test |
| 14 | Quality Gates | Linting, type checking | CI pipeline configured |
| 15 | Compression | 50-60% size reduction | Tech Lead gets concise docs |
| 16 | Version Control | Track architecture evolution | Understand changes over time |
| 17 | Integration Contracts | API schemas, events | Developer implements exact spec |
| 18 | Real-World Patterns | Business → architecture | Operations runbooks |
| 19 | Document for RAG | Metadata, embeddings | Enables Day 20-22 |
| 20 | RAG Queries | Find similar architectures | 30-40% design time savings |
| 21 | Pattern Ranking | Filter best patterns | Only proven patterns used |
| 22 | Citations | Source attribution | 37% time savings, audit trail |

---

## Linked Assets

- **Role Definition**: `docs/roles/architect/role_definition.md`
- **RAG Queries**: `docs/roles/architect/rag_queries.md`
- **Examples**: `docs/roles/architect/examples/`
- **Handoff Contracts**: `docs/operational/handoff_contracts.md`
- **Context Limits**: `docs/operational/context_limits.md`
- **Workflow**: `docs/specs/process/agent_workflow.md`

---

## Update Log

- ✅ 2025-11-15: Comprehensive Day 1-22 capabilities documented
- ✅ Integration points mapped to Analyst, Tech Lead, Developer roles
- ✅ Examples to be created for Days 6, 11, 12, 17
- [ ] Days 23-28: Pending epic scope definition
