<<<<<<< HEAD
# Handoff Contracts

## Purpose
Standardize input/output formats exchanged between roles to keep the agent
workflow predictable. Refer to `docs/specs/process/agent_workflow.md` for
sequence context.

## Analyst → Architect

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AnalystToArchitect",
  "type": "object",
  "required": ["epic", "requirements", "acceptance", "open_questions"],
  "properties": {
    "epic": { "type": "string", "pattern": "^EP\\d+$" },
    "requirements": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "title", "must_have", "should_have", "out_of_scope"],
        "properties": {
          "id": { "type": "string" },
          "title": { "type": "string" },
          "must_have": { "type": "array", "items": { "type": "string" } },
          "should_have": { "type": "array", "items": { "type": "string" } },
          "out_of_scope": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "acceptance": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "criterion", "evidence"],
        "properties": {
          "id": { "type": "string" },
          "criterion": { "type": "string" },
          "evidence": { "type": "string" }
        }
      }
    },
    "open_questions": { "type": "array", "items": { "type": "string" } },
    "attachments": { "type": "array", "items": { "type": "string", "format": "uri" } }
  }
}
```

## Architect → Tech Lead

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ArchitectToTechLead",
  "type": "object",
  "required": ["epic", "vision", "interfaces", "risks", "decisions"],
  "properties": {
    "epic": { "type": "string", "pattern": "^EP\\d+$" },
    "vision": { "type": "string" },
    "interfaces": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "purpose", "provider", "consumer"],
        "properties": {
          "name": { "type": "string" },
          "purpose": { "type": "string" },
          "provider": { "type": "string" },
          "consumer": { "type": "string" },
          "notes": { "type": "string" }
        }
      }
    },
    "risks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["description", "impact", "mitigation"],
        "properties": {
          "description": { "type": "string" },
          "impact": { "type": "string", "enum": ["low", "medium", "high"] },
          "mitigation": { "type": "string" }
        }
      }
    },
    "decisions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "status", "summary"],
        "properties": {
          "id": { "type": "string" },
          "status": { "type": "string", "enum": ["proposed", "accepted", "rejected"] },
          "summary": { "type": "string" },
          "link": { "type": "string", "format": "uri" }
        }
      }
    },
    "attachments": { "type": "array", "items": { "type": "string", "format": "uri" } }
  }
}
```

## Tech Lead → Developer

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TechLeadToDeveloper",
  "type": "object",
  "required": ["epic", "stages", "ci_gates", "handoff"],
  "properties": {
    "epic": { "type": "string", "pattern": "^EP\\d+$" },
    "stages": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["order", "name", "tasks", "dod"],
        "properties": {
          "order": { "type": "integer", "minimum": 1 },
          "name": { "type": "string" },
          "tasks": { "type": "array", "items": { "type": "string" } },
          "dod": { "type": "array", "items": { "type": "string" } },
          "evidence": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "ci_gates": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "command", "coverage"],
        "properties": {
          "name": { "type": "string" },
          "command": { "type": "string" },
          "coverage": { "type": "number", "minimum": 0, "maximum": 100 }
        }
      }
    },
    "risks": { "$ref": "#/$defs/risk" },
    "handoff": {
      "type": "object",
      "required": ["owner", "date", "checklist"],
      "properties": {
        "owner": { "type": "string" },
        "date": { "type": "string", "format": "date" },
        "checklist": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["item", "status"],
            "properties": {
              "item": { "type": "string" },
              "status": { "type": "string", "enum": ["pending", "in_progress", "complete"] }
            }
          }
        }
      }
    }
  },
  "$defs": {
    "risk": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["description", "owner", "status"],
        "properties": {
          "description": { "type": "string" },
          "owner": { "type": "string" },
          "status": { "type": "string", "enum": ["open", "mitigating", "closed"] }
        }
      }
    }
  }
}
```

## Developer → Reviewer

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DeveloperToReviewer",
  "type": "object",
  "required": ["epic", "changesets", "tests", "evidence"],
  "properties": {
    "epic": { "type": "string", "pattern": "^EP\\d+$" },
    "changesets": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "summary"],
        "properties": {
          "path": { "type": "string" },
          "summary": { "type": "string" },
          "tickets": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "tests": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["type", "command", "status", "coverage"],
        "properties": {
          "type": { "type": "string" },
          "command": { "type": "string" },
          "status": { "type": "string", "enum": ["pass", "fail", "skipped"] },
          "coverage": { "type": "number", "minimum": 0, "maximum": 100 },
          "artifacts": { "type": "array", "items": { "type": "string", "format": "uri" } }
        }
      }
    },
    "evidence": {
      "type": "array",
      "items": { "type": "string", "format": "uri" }
    },
    "notes": { "type": "string" }
  }
}
```

## Reviewer → Analyst (Closure Packet)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ReviewerToAnalyst",
  "type": "object",
  "required": ["epic", "decision", "findings", "follow_ups"],
  "properties": {
    "epic": { "type": "string", "pattern": "^EP\\d+$" },
    "decision": { "type": "string", "enum": ["approved", "rejected", "conditional"] },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "summary", "severity"],
        "properties": {
          "id": { "type": "string" },
          "summary": { "type": "string" },
          "severity": { "type": "string", "enum": ["info", "minor", "major", "critical"] },
          "evidence": { "type": "array", "items": { "type": "string", "format": "uri" } }
        }
      }
    },
    "follow_ups": { "type": "array", "items": { "type": "string" } },
    "archive_notes": { "type": "string" }
=======
# Handoff Contracts Between Roles

## Analyst → Architect

**Input Format (from Analyst):**
{
"epic_id": "EP19",
"requirements": [
{"id": "R-101", "text": "...", "type": "functional", "priority": "high"},
...
],
"clarity_score": 0.85,
"rag_citations": ["EP18_req#45", "EP15_req#12"],
"notes": "Requirements gathering complete; see reviews/analyst_review.md"
}

text

**Expected Architect Output:**
{
"epic_id": "EP19",
"requirements_id": "EP19_req_v1",
"architecture_vision": "...",
"components": [...],
"rag_citations": ["EP15_arch#decision-003"],
"questions_for_analyst": ["Q1", "Q2"] // If needed
}


**Token Budget:**
- Analyst output: ~2-3K tokens
- Available for Architect processing: ~9K tokens
- If Architect needs clarification: query Analyst again (loop back to Analyst)

## Architect → Tech Lead

[Similar structure...]

## Tech Lead → Developer

[Similar structure...]

## Developer → Reviewer (NEW - Day 23+)

**Input Format:**
{
"epic_id": "EP23",
"code_artifacts": [...],
"tests": [...],
"execution_logs": [...], // From Day 23 Observability
"decisions": [...], // From MADR
"metrics": {...} // From Day 27 Prometheus
}

---

## Real Handoff Examples

### Example 1: Analyst → Architect (EP23 Payment Module)

**Context:** Payment processing system requirements gathered over 2.5 hours, 18 exchanges, compressed to high clarity (0.87).

#### Analyst Output JSON:

```json
{
  "metadata": {
    "epic_id": "EP23",
    "analyst_agent": "cursor_analyst_v1",
    "timestamp": "2025-11-15T14:30:00Z",
    "version": "1.0",
    "session_duration_hours": 2.5,
    "total_exchanges": 18,
    "compression_applied": true,
    "compressed_from_tokens": 7800,
    "final_tokens": 2100
  },

  "requirements": [
    {
      "id": "REQ-PAY-001",
      "text": "System must process credit card payments via Stripe API",
      "type": "functional",
      "priority": "high",
      "clarity_score": 0.91,
      "acceptance_criteria": [
        "Transaction processed in < 2 seconds (p95)",
        "PCI DSS Level 1 compliance maintained",
        "Successful transactions logged with timestamp and transaction ID",
        "Failed transactions trigger retry logic (max 3 attempts)"
      ],
      "dependencies": ["Stripe API integration", "Database transaction log"],
      "out_of_scope": ["Cryptocurrency payments (Phase 2)"]
    },
    {
      "id": "REQ-PAY-002",
      "text": "Support multiple payment methods: credit cards (Visa, MC, AmEx), PayPal, bank transfer",
      "type": "functional",
      "priority": "high",
      "clarity_score": 0.88,
      "acceptance_criteria": [
        "Provider abstraction layer supports pluggable payment providers",
        "Fallback to secondary provider if primary fails (< 5s failover)",
        "Provider health checks run every 30 seconds"
      ],
      "rag_citation": {
        "source_epic": "EP19",
        "source_req": "R-78",
        "similarity_score": 0.89,
        "reason": "Similar multi-provider architecture from EP19 payment gateway"
      }
    },
    {
      "id": "REQ-PAY-003",
      "text": "Multi-currency support: USD, EUR, GBP with real-time exchange rates",
      "type": "functional",
      "priority": "high",
      "clarity_score": 0.85,
      "acceptance_criteria": [
        "Currency conversion via third-party API (e.g., exchangerate-api.com)",
        "Exchange rates cached for 1 hour",
        "All amounts stored in cents/pence (integer) to avoid floating point errors"
      ]
    },
    {
      "id": "REQ-PAY-004",
      "text": "Refund processing: 14-day refund window, partial and full refunds supported",
      "type": "functional",
      "priority": "medium",
      "clarity_score": 0.87,
      "acceptance_criteria": [
        "Refund request triggers workflow approval (> $500 requires manager approval)",
        "Refund processed within 5-7 business days",
        "Customer notified via email on refund initiation and completion"
      ]
    },
    {
      "id": "REQ-PAY-005",
      "text": "Payment reconciliation: Daily reports matching transactions to bank settlements",
      "type": "functional",
      "priority": "medium",
      "clarity_score": 0.82,
      "acceptance_criteria": [
        "Automated reconciliation job runs at 00:00 UTC daily",
        "Discrepancies flagged for manual review",
        "Report exported to CSV and sent to finance team"
      ]
    },
    {
      "id": "REQ-SEC-001",
      "text": "Payment data security: PCI DSS Level 1 compliance",
      "type": "constraint",
      "priority": "critical",
      "clarity_score": 0.93,
      "acceptance_criteria": [
        "Card numbers never stored in database (tokenized via Stripe)",
        "All payment API calls over HTTPS with TLS 1.3",
        "Payment audit log encrypted at rest (AES-256)",
        "Annual PCI DSS audit passed"
      ]
    },
    {
      "id": "REQ-PERF-001",
      "text": "Payment processing performance: < 2s transaction time, 10K concurrent transactions",
      "type": "non-functional",
      "priority": "high",
      "clarity_score": 0.89,
      "acceptance_criteria": [
        "Transaction processing: < 2 seconds (p95), < 3 seconds (p99)",
        "System handles 10,000 concurrent transactions without degradation",
        "Database query optimization: payment lookup < 100ms"
      ],
      "rag_citation": {
        "source_epic": "EP15",
        "source_req": "R-42",
        "similarity_score": 0.92,
        "reason": "Proven performance targets from EP15 payment API"
      }
    },
    {
      "id": "REQ-INFRA-001",
      "text": "Integration with shared infrastructure (MongoDB, Prometheus, Grafana)",
      "type": "constraint",
      "priority": "critical",
      "clarity_score": 0.95,
      "acceptance_criteria": [
        "Payment data stored in shared MongoDB cluster",
        "Expose /metrics endpoint for Prometheus scraping",
        "Grafana dashboard shows: transaction rate, success rate, latency (p50/p95/p99)",
        "Structured logs sent to Loki"
      ],
      "source": "docs/operational/shared_infra.md"
    }
  ],

  "summary": {
    "total_requirements": 8,
    "functional": 5,
    "non_functional": 1,
    "constraints": 2,
    "clarity_score": 0.87,
    "completeness_score": 0.92
  },

  "rag_summary": {
    "queries_performed": 2,
    "total_citations": 2,
    "token_cost": 450,
    "patterns_reused": [
      "Multi-provider payment architecture (EP19)",
      "Performance targets (EP15)"
    ]
  },

  "open_questions": [
    {
      "id": "Q-001",
      "text": "Should we support Apple Pay and Google Pay in MVP?",
      "stakeholder": "Product Owner",
      "priority": "medium",
      "status": "pending",
      "blocking": false
    },
    {
      "id": "Q-002",
      "text": "Maximum transaction amount limit?",
      "stakeholder": "Finance Team",
      "priority": "high",
      "status": "pending",
      "blocking": true
    }
  ],

  "decisions": [
    {
      "id": "DEC-001",
      "text": "Use Stripe as primary payment provider",
      "rationale": "PCI compliance handled by Stripe, proven reliability, good API documentation",
      "approved_by": "CTO",
      "date": "2025-11-15"
    },
    {
      "id": "DEC-002",
      "text": "Store amounts as integers (cents) not floats",
      "rationale": "Avoids floating point rounding errors in currency calculations",
      "approved_by": "Tech Lead",
      "date": "2025-11-15"
    }
  ],

  "notes": "Requirements gathering complete. Leveraged patterns from EP15 (payment performance) and EP19 (multi-provider architecture). Two blocking questions remain (Q-002: transaction limits). Estimated implementation: 6-8 weeks. High complexity due to PCI compliance requirements."
}
```

#### Expected Architect Response:

```json
{
  "metadata": {
    "epic_id": "EP23",
    "architect_agent": "cursor_architect_v1",
    "timestamp": "2025-11-16T10:00:00Z",
    "requirements_version": "1.0",
    "time_spent_hours": 4.5
  },

  "architecture_vision": "Microservice-based payment processing system with provider abstraction layer. Follows EP19 multi-provider pattern with enhancements for currency handling. Clean Architecture: domain layer (payment entities), application layer (use cases), infrastructure layer (Stripe adapter, PayPal adapter).",

  "components": [
    {
      "name": "PaymentService",
      "type": "microservice",
      "responsibilities": [
        "Payment transaction orchestration",
        "Provider selection and failover",
        "Transaction logging and audit"
      ],
      "interfaces": {
        "rest_api": "POST /api/v1/payments",
        "events": ["PaymentCompleted", "PaymentFailed", "RefundInitiated"]
      },
      "dependencies": ["ProviderAdapter", "TransactionLog", "MongoDB"]
    },
    {
      "name": "ProviderAdapter",
      "type": "abstraction_layer",
      "responsibilities": [
        "Abstract payment provider details",
        "Health checks and failover logic",
        "Provider-specific error mapping"
      ],
      "implementations": ["StripeAdapter", "PayPalAdapter", "BankTransferAdapter"]
    },
    {
      "name": "CurrencyConverter",
      "type": "service",
      "responsibilities": [
        "Real-time exchange rate fetching",
        "Rate caching (1-hour TTL)",
        "Currency conversion calculations"
      ]
    },
    {
      "name": "RefundProcessor",
      "type": "service",
      "responsibilities": [
        "Refund workflow management",
        "Approval routing (> $500)",
        "Email notifications"
      ]
    }
  ],

  "data_model": {
    "collections": [
      {
        "name": "payments",
        "schema": {
          "transaction_id": "UUID",
          "amount_cents": "Integer (not Float!)",
          "currency": "String (USD/EUR/GBP)",
          "provider": "String (stripe/paypal)",
          "status": "Enum (pending/completed/failed/refunded)",
          "created_at": "Timestamp",
          "updated_at": "Timestamp"
        },
        "indexes": [
          "transaction_id (unique)",
          "status + created_at",
          "provider + status"
        ]
      }
    ]
  },

  "architectural_decisions": [
    {
      "id": "MADR-067",
      "title": "Use provider abstraction layer for payment providers",
      "status": "accepted",
      "context": "REQ-PAY-002 requires multi-provider support with failover",
      "decision": "Implement ProviderAdapter interface with pluggable implementations",
      "consequences": [
        "Easier to add new providers",
        "Failover logic centralized",
        "Slight performance overhead (abstraction layer)"
      ],
      "alternatives": ["Direct provider integration (rejected: tight coupling)"]
    },
    {
      "id": "MADR-068",
      "title": "Store amounts as integer cents to avoid floating point errors",
      "status": "accepted",
      "context": "DEC-002 from Analyst, standard practice for financial calculations",
      "decision": "All amounts stored as Integer (cents/pence), convert to decimal for display only",
      "consequences": [
        "No rounding errors in calculations",
        "Database schema uses BIGINT not DECIMAL",
        "Conversion logic needed at API boundary"
      ]
    }
  ],

  "rag_citations": [
    {
      "source_epic": "EP19",
      "architecture_reference": "MADR-045: Multi-provider payment architecture",
      "reused_patterns": ["ProviderAdapter interface", "Health check strategy"],
      "implementation_reference": "src/infrastructure/adapters/payment/"
    },
    {
      "source_epic": "EP15",
      "architecture_reference": "MADR-023: Payment service performance optimization",
      "reused_patterns": ["Database indexing strategy", "Query optimization"]
    }
  ],

  "questions_resolved": [
    {
      "analyst_question_id": "Q-001",
      "answer": "Apple Pay and Google Pay: Phase 2. MVP focuses on Stripe + PayPal + Bank Transfer.",
      "rationale": "Reduces scope, accelerates MVP delivery. Digital wallets can use same ProviderAdapter pattern later."
    }
  ],

  "questions_for_analyst": [
    {
      "id": "ARCH-Q-001",
      "text": "Q-002 (transaction limits) is blocking. Need answer before finalizing rate limiting design.",
      "priority": "high",
      "blocking": true
    }
  ],

  "risks": [
    {
      "id": "RISK-001",
      "description": "PCI DSS Level 1 compliance audit timeline unclear",
      "impact": "high",
      "likelihood": "medium",
      "mitigation": "Stripe handles most PCI compliance. We audit our audit log encryption and access controls only.",
      "owner": "Security Team"
    },
    {
      "id": "RISK-002",
      "description": "Currency API (exchangerate-api.com) rate limits and reliability",
      "impact": "medium",
      "likelihood": "low",
      "mitigation": "Cache rates for 1 hour, fallback to previous day's rates if API unavailable",
      "owner": "DevOps"
    }
  ],

  "implementation_estimate": {
    "duration_weeks": 7,
    "team_size": 3,
    "breakdown": {
      "PaymentService": "2 weeks",
      "ProviderAdapters": "2 weeks",
      "CurrencyConverter": "1 week",
      "RefundProcessor": "1 week",
      "Testing + Integration": "1 week"
    }
  },

  "notes": "Architecture follows Clean Architecture principles and reuses proven patterns from EP15 and EP19. Blocking question (Q-002: transaction limits) must be resolved before Tech Lead can finalize rate limiting design. Estimated 7 weeks implementation with 3-person team. PCI compliance risk mitigated by using Stripe for card tokenization."
}
```

---

### Example 2: Architect → Tech Lead (EP23 Payment Module)

**Context:** Architect completed design in 4.5 hours, addressing Analyst requirements with architectural decisions.

#### Tech Lead Input (from Architect):

```json
{
  "epic_id": "EP23",
  "requirements_id": "EP23_req_v1",
  "architecture_id": "EP23_arch_v1",
  "components": [...],  // As above
  "architectural_decisions": [...],  // MADR-067, MADR-068
  "implementation_estimate": "7 weeks, 3-person team"
}
```

#### Tech Lead Output (Implementation Plan):

```json
{
  "metadata": {
    "epic_id": "EP23",
    "tech_lead_agent": "cursor_tech_lead_v1",
    "timestamp": "2025-11-17T09:00:00Z",
    "architecture_version": "1.0",
    "plan_version": "1.0"
  },

  "stages": [
    {
      "stage_id": "STAGE-1",
      "name": "Foundation & Shared Infrastructure Setup",
      "duration_days": 3,
      "owner": "DevOps",
      "status": "pending",
      "tasks": [
        "Set up MongoDB payment database and collections",
        "Configure Prometheus metrics endpoints",
        "Create Grafana dashboard templates",
        "Set up CI/CD pipeline for payment service"
      ],
      "dod": [
        "MongoDB cluster accessible with credentials",
        "Prometheus scraping payment service /metrics",
        "Grafana dashboard deployed to shared Grafana",
        "CI pipeline runs lint + tests + coverage"
      ],
      "evidence": ["MongoDB connection test passed", "Grafana dashboard screenshot"],
      "dependencies": [],
      "blockers": []
    },
    {
      "stage_id": "STAGE-2",
      "name": "PaymentService Core & Domain Layer",
      "duration_days": 7,
      "owner": "Developer A",
      "status": "pending",
      "tasks": [
        "Implement Payment entity (domain layer)",
        "Implement Transaction value objects",
        "Create PaymentRepository interface",
        "Implement payment use cases (ProcessPayment, RefundPayment)"
      ],
      "dod": [
        "Payment entity with validation logic",
        "Unit tests for domain layer (100% coverage)",
        "Use cases pass acceptance criteria (REQ-PAY-001)"
      ],
      "ci_gates": ["lint", "unit_tests", "coverage >= 80%"],
      "dependencies": ["STAGE-1"],
      "blockers": []
    },
    {
      "stage_id": "STAGE-3",
      "name": "ProviderAdapter Abstraction Layer",
      "duration_days": 7,
      "owner": "Developer B",
      "status": "pending",
      "tasks": [
        "Define ProviderAdapter interface (MADR-067)",
        "Implement StripeAdapter",
        "Implement PayPalAdapter",
        "Implement health check and failover logic (REQ-PAY-002)"
      ],
      "dod": [
        "ProviderAdapter interface documented",
        "StripeAdapter passes integration tests",
        "Failover completes in < 5s (REQ-PAY-002 AC)"
      ],
      "ci_gates": ["integration_tests", "performance_test (failover < 5s)"],
      "dependencies": ["STAGE-2"],
      "blockers": ["Need Stripe test API keys (DevOps)"]
    },
    {
      "stage_id": "STAGE-4",
      "name": "CurrencyConverter Service",
      "duration_days": 5,
      "owner": "Developer C",
      "status": "pending",
      "tasks": [
        "Integrate exchangerate-api.com",
        "Implement 1-hour rate caching (REQ-PAY-003 AC)",
        "Handle API failures gracefully",
        "Implement integer cents conversion (MADR-068)"
      ],
      "dod": [
        "Currency conversion accurate within 0.01%",
        "Cache hit rate > 95%",
        "Fallback to previous rates if API down"
      ],
      "ci_gates": ["integration_tests", "cache_performance_test"],
      "dependencies": ["STAGE-2"],
      "blockers": []
    },
    {
      "stage_id": "STAGE-5",
      "name": "Performance Optimization & Load Testing",
      "duration_days": 5,
      "owner": "Developer A",
      "status": "pending",
      "tasks": [
        "Database query optimization (REQ-PERF-001)",
        "Add database indexes (transaction_id, status + created_at)",
        "Load testing: 10K concurrent transactions",
        "Optimize to meet < 2s p95 latency"
      ],
      "dod": [
        "Transaction processing < 2s (p95) - REQ-PERF-001 AC",
        "Load test passes: 10K concurrent without degradation",
        "Database queries < 100ms (REQ-PERF-001 AC)"
      ],
      "ci_gates": ["load_tests", "performance_benchmarks"],
      "dependencies": ["STAGE-3", "STAGE-4"],
      "blockers": []
    },
    {
      "stage_id": "STAGE-6",
      "name": "Security & PCI Compliance",
      "duration_days": 5,
      "owner": "Security Team + Developer B",
      "status": "pending",
      "tasks": [
        "Ensure card data never stored (tokenized via Stripe) - REQ-SEC-001 AC",
        "Implement audit log encryption (AES-256) - REQ-SEC-001 AC",
        "Set up HTTPS with TLS 1.3",
        "Security audit and penetration testing"
      ],
      "dod": [
        "Security audit passed",
        "Penetration test report clean",
        "Audit log encrypted at rest (verified)",
        "All API calls HTTPS only"
      ],
      "ci_gates": ["security_scan", "audit_log_encryption_test"],
      "dependencies": ["STAGE-3"],
      "blockers": ["Security team availability (schedule audit)"]
    },
    {
      "stage_id": "STAGE-7",
      "name": "Integration Tests & E2E Testing",
      "duration_days": 5,
      "owner": "QA + All Developers",
      "status": "pending",
      "tasks": [
        "Integration tests for all acceptance criteria",
        "E2E tests: payment flow, refund flow, failover",
        "Test multi-currency conversions",
        "Test error scenarios (provider down, network timeout)"
      ],
      "dod": [
        "All acceptance criteria have passing tests",
        "E2E tests cover happy path and error paths",
        "Test coverage ≥ 80%"
      ],
      "ci_gates": ["integration_tests", "e2e_tests", "coverage >= 80%"],
      "dependencies": ["STAGE-5", "STAGE-6"],
      "blockers": []
    },
    {
      "stage_id": "STAGE-8",
      "name": "Deployment & Monitoring Setup",
      "duration_days": 3,
      "owner": "DevOps + Tech Lead",
      "status": "pending",
      "tasks": [
        "Deploy to staging environment",
        "Configure Prometheus alerts (error rate > 1%, latency > 3s)",
        "Smoke tests in staging",
        "Production deployment (canary rollout)"
      ],
      "dod": [
        "Smoke tests pass in staging",
        "Prometheus alerts configured and tested",
        "Production deployment successful (0 downtime)",
        "Rollback plan tested"
      ],
      "ci_gates": ["smoke_tests_staging", "smoke_tests_production"],
      "dependencies": ["STAGE-7"],
      "blockers": []
    }
  ],

  "timeline": {
    "total_duration_days": 40,
    "total_duration_weeks": 8,
    "critical_path": ["STAGE-1", "STAGE-2", "STAGE-3", "STAGE-5", "STAGE-7", "STAGE-8"],
    "parallel_stages": [
      ["STAGE-3", "STAGE-4"]
    ]
  },

  "risk_register": [
    {
      "id": "PLAN-RISK-001",
      "description": "Stripe test API keys delay (blocker for STAGE-3)",
      "impact": "high",
      "likelihood": "low",
      "mitigation": "Request keys from DevOps immediately, use mock adapter if delayed",
      "owner": "DevOps",
      "status": "open"
    },
    {
      "id": "PLAN-RISK-002",
      "description": "Security audit scheduling (blocker for STAGE-6)",
      "impact": "medium",
      "likelihood": "medium",
      "mitigation": "Book security team 2 weeks in advance, have checklist ready",
      "owner": "Tech Lead",
      "status": "open"
    }
  ],

  "ci_gates": [
    {"name": "lint", "command": "make lint", "required": true},
    {"name": "unit_tests", "command": "make test-unit", "required": true},
    {"name": "integration_tests", "command": "make test-integration", "required": true},
    {"name": "coverage", "command": "make coverage", "threshold": "80%", "required": true},
    {"name": "security_scan", "command": "make security-scan", "required": true},
    {"name": "load_tests", "command": "make load-test", "required": true},
    {"name": "smoke_tests_staging", "command": "make smoke-test-staging", "required": true},
    {"name": "smoke_tests_production", "command": "make smoke-test-prod", "required": true}
  ],

  "team_allocation": {
    "Developer A": ["STAGE-2", "STAGE-5"],
    "Developer B": ["STAGE-3", "STAGE-6"],
    "Developer C": ["STAGE-4"],
    "DevOps": ["STAGE-1", "STAGE-8"],
    "QA": ["STAGE-7"]
  },

  "notes": "8-week plan (revised from Architect's 7-week estimate due to security audit time). Critical path: STAGE-1 → STAGE-2 → STAGE-3 → STAGE-5 → STAGE-7 → STAGE-8. STAGE-3 and STAGE-4 can run in parallel. Two blockers identified: Stripe API keys (STAGE-3) and security audit scheduling (STAGE-6). Plan accounts for all 8 requirements and 2 MADRs from Architect."
}
```

---

## Handoff Quality Metrics

### Example 1: Analyst → Architect

**Quality Indicators:**
```
✅ Clarity Score: 0.87 (high)
✅ Completeness: 8/8 requirements with acceptance criteria
✅ RAG Citations: 2 (reused proven patterns)
✅ Open Questions: 2 (1 blocking, 1 non-blocking)
✅ Decisions: 2 (CTO + Tech Lead approved)
✅ Compression: Applied (7800 → 2100 tokens)
```

**Architect Response Time:** 4.5 hours (expected: 6-8 hours)
**Clarification Requests:** 1 (Q-002 transaction limits)
**Handoff Success:** ✅ High quality (minimal back-and-forth)

---

### Example 2: Architect → Tech Lead

**Quality Indicators:**
```
✅ Components: 4 (clearly defined)
✅ MADRs: 2 (architectural decisions documented)
✅ RAG Citations: 2 (referenced EP15 and EP19)
✅ Risks: 2 (identified with mitigations)
✅ Implementation Estimate: 7 weeks (detailed breakdown)
```

**Tech Lead Response Time:** 3 hours (expected: 4-6 hours)
**Clarification Requests:** 0 (all information provided)
**Handoff Success:** ✅ Excellent (no back-and-forth needed)

---

## Key Patterns for High-Quality Handoffs

### 1. Complete Metadata

```json
{
  "metadata": {
    "epic_id": "EPXX",
    "agent": "role_agent_v1",
    "timestamp": "ISO-8601",
    "version": "1.0",
    "time_spent_hours": X.X,
    "compression_applied": true/false
  }
}
```

### 2. RAG Citations for Pattern Reuse

```json
{
  "rag_citation": {
    "source_epic": "EPXX",
    "source_req": "R-XX",
    "similarity_score": 0.XX,
    "reason": "Clear explanation",
    "production_validated": true
  }
}
```

### 3. Open Questions with Status

```json
{
  "open_questions": [
    {
      "id": "Q-XXX",
      "text": "Specific question",
      "stakeholder": "Who to ask",
      "priority": "high/medium/low",
      "blocking": true/false,
      "status": "pending/resolved"
    }
  ]
}
```

### 4. Traceability Chain

```
Analyst REQ-PAY-001
  → Architect Component: PaymentService
  → Architect MADR-067
  → Tech Lead STAGE-2
  → Developer Implementation
  → Tests: test_payment_processing.py
```

---

## Common Handoff Issues & Solutions

### Issue 1: Ambiguous Requirements

**Problem:**
```json
{
  "text": "System should be fast",
  "clarity_score": 0.35
}
```

**Solution:**
```json
{
  "text": "Transaction processing must complete in < 2 seconds (p95)",
  "clarity_score": 0.91,
  "acceptance_criteria": ["Measured via Prometheus latency metrics"]
}
```

---

### Issue 2: Missing Dependencies

**Problem:**
```json
{
  "components": ["PaymentService"],
  "dependencies": []  // Missing!
}
```

**Solution:**
```json
{
  "components": ["PaymentService"],
  "dependencies": ["Stripe API", "MongoDB", "Prometheus"]
}
```

---

### Issue 3: No RAG Citations (Missing Context)

**Problem:**
```json
{
  "requirements": [
    {"text": "Support multiple payment providers"}
  ]
  // No context from past epics
}
```

**Solution:**
```json
{
  "requirements": [
    {
      "text": "Support multiple payment providers",
      "rag_citation": {
        "source_epic": "EP19",
        "reason": "Reuse proven multi-provider architecture",
        "implementation_reference": "src/infrastructure/adapters/payment/"
      }
    }
  ]
}
```
---

## Architect → Tech Lead: Additional Considerations

**MADR Quality Requirements:**
- Include: Context, Decision, Alternatives (min 2), Consequences (positive + negative)
- Link to requirements: "Addresses REQ-XXX"
- Production validation status if reusing patterns

**Architecture Document Checklist:**
- [ ] All components mapped to requirements
- [ ] Clean Architecture boundaries defined
- [ ] Cross-cutting concerns addressed (logging, metrics, config)
- [ ] Deployment topology specified
- [ ] Integration contracts published
- [ ] Min 2 MADRs for complex epics

**See Examples:**
- Detailed: `docs/operational/handoff_contracts.md#example-1` (Analyst→Architect→Tech Lead full chain)
- Architecture validation: `docs/roles/architect/examples/day_6_cot_validation.md`

---

## Developer → Reviewer Handoff

### Purpose
Developer hands off completed implementation with tests, documentation, and CI evidence to Reviewer for quality assurance.

### Contract Format

```json
{
  "metadata": {
    "epic_id": "EP23",
    "stage": "Stage 3 – Payment Refund Module",
    "developer": "developer_1",
    "handoff_timestamp": "2025-11-15T14:45:00Z",
    "branch": "feature/ep23-payment-refund",
    "pr_number": "PR-456"
  },
  "implementation": {
    "tasks_completed": [
      {
        "task_id": "TASK-42",
        "title": "Implement payment refund logic",
        "status": "completed",
        "dod_checklist": [
          { "item": "RefundPaymentUseCase implemented", "status": "done" },
          { "item": "Unit tests: 100% coverage", "status": "done" },
          { "item": "Integration test with Stripe sandbox", "status": "done" }
        ]
      }
    ],
    "files_changed": [
      {
        "path": "src/application/use_cases/refund_payment.py",
        "lines_added": 78,
        "lines_deleted": 0,
        "purpose": "Refund payment use case implementation"
      },
      {
        "path": "src/domain/entities/refund.py",
        "lines_added": 42,
        "lines_deleted": 0,
        "purpose": "Refund domain entity"
      },
      {
        "path": "tests/unit/application/test_refund_payment.py",
        "lines_added": 145,
        "lines_deleted": 0,
        "purpose": "Unit tests for refund use case"
      },
      {
        "path": "tests/integration/test_refund_flow.py",
        "lines_added": 68,
        "lines_deleted": 0,
        "purpose": "Integration tests with Stripe"
      }
    ]
  },
  "test_evidence": {
    "unit_tests": {
      "command": "pytest tests/unit/application/test_refund_payment.py -v --cov=src/application/use_cases/refund_payment",
      "status": "passed",
      "test_count": 12,
      "failed_count": 0,
      "coverage_percent": 100.0,
      "duration_ms": 850,
      "executed_at": "2025-11-15T14:30:00Z"
    },
    "integration_tests": {
      "command": "pytest tests/integration/test_refund_flow.py -v",
      "status": "passed",
      "test_count": 4,
      "failed_count": 0,
      "duration_ms": 2400,
      "executed_at": "2025-11-15T14:35:00Z"
    },
    "linter_results": {
      "black": "✓ All files formatted (88 char line length)",
      "flake8": "✓ 0 errors, 0 warnings",
      "mypy": "✓ Type checking passed (strict mode)"
    }
  },
  "ci_evidence": {
    "pipeline_url": "https://gitlab.com/project/pipelines/12345",
    "status": "passed",
    "stages": [
      { "name": "lint", "status": "passed", "duration_ms": 3200 },
      { "name": "unit_tests", "status": "passed", "duration_ms": 5800 },
      { "name": "integration_tests", "status": "passed", "duration_ms": 12000 },
      { "name": "coverage_report", "status": "passed", "coverage": 92.5 }
    ],
    "artifacts": [
      "coverage_report.html",
      "test_results.xml",
      "linter_output.txt"
    ]
  },
  "documentation": {
    "docstrings": "All public functions have docstrings (Google style)",
    "readme_updated": false,
    "architecture_impact": "None – follows existing Clean Architecture pattern"
  },
  "code_reuse": {
    "citations": [
      {
        "source_epic": "EP19",
        "source_file": "src/infrastructure/adapters/stripe_adapter.py",
        "adapted_pattern": "Stripe API error handling",
        "reason": "Proven pattern with 0 bugs in production"
      }
    ]
  },
  "review_checklist": {
    "items": [
      { "item": "Code follows Clean Architecture (domain/application/infrastructure)", "status": "ready" },
      { "item": "All functions ≤15 lines where possible", "status": "ready" },
      { "item": "Type hints: 100% coverage", "status": "ready" },
      { "item": "Docstrings for all public functions", "status": "ready" },
      { "item": "Unit tests: ≥80% coverage (actual: 100%)", "status": "ready" },
      { "item": "Integration tests pass", "status": "ready" },
      { "item": "No print() statements (use logging)", "status": "ready" },
      { "item": "No hardcoded secrets", "status": "ready" },
      { "item": "Error handling with specific exceptions", "status": "ready" },
      { "item": "Logging with structured context", "status": "ready" }
    ]
  },
  "notes": "Refund logic follows Stripe's API flow. Edge case: partial refunds handled in separate task (TASK-48). All critical paths tested."
}
```

---

### Expected Reviewer Response

```json
{
  "review_id": "REV-123",
  "epic_id": "EP23",
  "pr_number": "PR-456",
  "reviewer": "reviewer_agent",
  "status": "approved_with_comments",
  "reviewed_at": "2025-11-15T15:30:00Z",
  "review_result": {
    "architecture_pass": {
      "status": "approved",
      "findings": [
        "✓ Clean Architecture boundaries respected",
        "✓ Domain layer has no external dependencies",
        "✓ Use case orchestrates correctly"
      ]
    },
    "component_pass": {
      "status": "approved_with_minor_comments",
      "findings": [
        "✓ RefundPaymentUseCase: Well-structured",
        "⚠ Refund entity: Consider adding `refunded_at` timestamp field",
        "✓ Error handling: Comprehensive"
      ]
    },
    "synthesis_pass": {
      "status": "approved",
      "overall_quality": 0.92,
      "test_coverage": 100.0,
      "code_complexity": "Low (avg 3.2 per function)",
      "maintainability_index": 87
    }
  },
  "comments": [
    {
      "severity": "minor",
      "file": "src/domain/entities/refund.py",
      "line": 15,
      "comment": "Consider adding `refunded_at: datetime` field for audit trail",
      "action_required": "optional"
    }
  ],
  "approval": {
    "approved": true,
    "merge_ready": true,
    "conditions": ["Address minor comment in follow-up PR"]
  },
  "metrics": {
    "review_duration_minutes": 45,
    "issues_found": 1,
    "critical_issues": 0,
    "architecture_violations": 0
>>>>>>> origin/master
  }
}
```

<<<<<<< HEAD
## Integration Notes
- Embed schemas in CI validation routines before handoffs.
- Store rendered payloads under respective role `examples/` folders.
- Revisit schemas after each new epic to capture evolving needs.
=======
---

### Handoff Quality Metrics

**Developer → Reviewer Quality Indicators:**
- ✅ All CI gates passed before handoff
- ✅ Test coverage ≥ 80% (target: 90%+)
- ✅ 0 linter errors
- ✅ All DoD items checked
- ✅ Code citations included (if reusing patterns)

**Expected Review Turnaround:**
- Simple PR (<200 lines): 1-2 hours
- Medium PR (200-500 lines): 2-4 hours
- Complex PR (>500 lines): 4-8 hours

**Review Quality Indicators:**
- Architecture violations found: 0 (target)
- Critical issues found: 0 (target)
- Minor issues found: ≤3 (acceptable)
- Overall quality score: ≥0.85 (target)

---

### Real Example: EP23 Payment Refund Module

**Developer Handoff Checklist:**
- [x] Feature branch created: `feature/ep23-payment-refund`
- [x] All task DoD items completed
- [x] Unit tests: 100% coverage (12 tests, all passed)
- [x] Integration tests: 4 tests, all passed
- [x] CI pipeline: All stages passed
- [x] Linter: 0 errors, 0 warnings
- [x] Type checker: 100% strict mode compliance
- [x] Docstrings: All public functions documented
- [x] Code citations: 1 pattern adapted from EP19
- [x] PR created: PR-456
- [x] Handoff JSON generated and committed

**Result:** Reviewer approved with 1 minor comment (non-blocking), merged to main in 2 hours.

---

## Developer → Reviewer Best Practices

### Before Handoff
1. **Self-Review:** Read your own code as if you're the reviewer
2. **Run Full CI Locally:** `make test && make lint && make coverage`
3. **Check Diff:** Review `git diff main` for unintended changes
4. **Test Manually:** Run the feature end-to-end in local environment
5. **Update Handoff JSON:** Include all evidence and checklist items

### During Handoff
- **Be Explicit:** Link to CI pipeline, test reports, coverage reports
- **Provide Context:** Explain non-obvious decisions in PR description
- **Cite Sources:** If adapted from past code, cite epic and reason
- **Flag Risks:** Note any potential edge cases or limitations

### After Review
- **Address Comments Promptly:** Critical → same day, Minor → next day
- **Acknowledge All Feedback:** Even if you disagree, explain reasoning
- **Update Tests:** If reviewer found gaps, add tests immediately
- **Close Loop:** Confirm with reviewer before merging

---

## Linked Resources
- Analyst → Architect: `#analyst-architect-handoff`
- Architect → Tech Lead: `#architect-tech-lead-handoff`
- Tech Lead → Developer: `#tech-lead-developer-handoff`
- Role Definitions: `docs/roles/*/role_definition.md`
>>>>>>> origin/master
