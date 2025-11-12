# Agent Roles · Overview
> Style: EN only, concise. Use bullets/tables; avoid narrative prose.

This directory defines the roles and responsibilities for the AI-assisted development workflow.

## 🎭 Role Hierarchy

```
Analyst (1-pager) → Architect (3-pager) → Tech Lead (6-pager) → Developer (code)
         ↓                ↓                      ↓                    ↓
    Requirements    Architecture         Implementation         Working Code
                     Vision                  Plan
```

## 📋 Amazon X-Pager Standards

| Role | Document Length | Purpose |
|------|----------------|---------|
| **Analyst** | 1-pager | Requirements: problem, scope, success criteria |
| **Architect** | 3-pager | Vision: components, boundaries, interfaces, security |
| **Tech Lead** | 6-pager | Plan: stages, testing, deployment, CI/CD, risks |
| **Developer** | No limit | Code: implementation, tests, worklogs, ADRs |

## 📚 Role Specifications

### [Analyst](analyst.md)
- **Purpose**: Define requirements and ensure specs are testable
- **Outputs**: 1-pager with Must/Should/Out of Scope
- **Reviews**: Architecture (3-pager) and Plan (6-pager)
- **Model**: Claude 3.5 Sonnet (requirements elicitation, clarity)

### [Architect](architect.md)
- **Purpose**: Produce architectural vision and contracts
- **Outputs**: 3-pager with components, boundaries, interfaces, security
- **Reviews**: Tech Lead plan for architectural compliance
- **Model**: Claude 3.5 Sonnet (design patterns, trade-offs)

### [Tech Lead](tech_lead.md)
- **Purpose**: Translate architecture into actionable implementation plan
- **Outputs**: 6-pager with stages, testing, deployment, CI/CD
- **Reviews**: Implementation for compliance with plan
- **Model**: Claude 3.5 Sonnet (planning, orchestration, risk management)

### [Developer](developer.md)
- **Purpose**: Implement with tests-first approach
- **Outputs**: Code, tests, worklogs, ADRs
- **Reviews**: Peer code review, address feedback
- **Model**: Claude 3.5 Sonnet (code generation, refactoring)

## 🔄 Workflow

### Phase 1: Planning (concise)
1. **Analyst** creates 1-pager with requirements
2. **Architect** creates 3-pager with vision, interfaces, security
3. **Tech Lead** creates 6-pager with implementation plan
4. **Analyst** reviews and consolidates feedback
5. Team approves final plan

### Phase 2: Implementation (concise)
1. **Developer** implements following plan (TDD, tests first)
2. **Developer** maintains worklog and ADRs
3. **Developer** submits PRs for peer review
4. **Tech Lead** validates CI gates passing
5. **Architect** validates architectural compliance (high-level)

### Phase 3: Review
1. **Tech Lead** verifies implementation matches plan
2. **Architect** validates layer boundaries and interfaces
3. **Analyst** confirms acceptance criteria met
4. **Developer** addresses feedback and fixes issues

### Phase 4: Closure
1. **Developer** completes final fixes
2. **Tech Lead** confirms deployment readiness
3. **Analyst** writes epic summary and archives docs
4. Team conducts retrospective

## Auto Mode Policy (All Roles)
- Use auto for templated, low‑risk generation (skeletons, checklists, scaffolds).
- Never auto‑approve or expand scope; human review required.
- Decisions impacting architecture/CI gates → create a MADR.
- Mark auto‑generated content; keep within page/length limits.

## 🎯 Clear Boundaries

### What Each Role Does NOT Do

| Role | Out of Scope |
|------|-------------|
| **Analyst** | ❌ Solution design, architecture, implementation |
| **Architect** | ❌ Sprint planning, testing strategy, deployment, code review |
| **Tech Lead** | ❌ Requirements, architecture design, code implementation |
| **Developer** | ❌ Scope changes, architecture decisions, plan changes |

## 🤖 Model Recommendations (Cursor Available Models)

| Role | Primary Model | Alternative | Avoid |
|------|--------------|-------------|-------|
| **Analyst** | GPT-5 | Haiku 4.5 | Composer-1, Grok Code |
| **Architect** | Sonnet 4.5 | GPT-5 | Composer-1, Grok Code, Haiku 4.5 |
| **Tech Lead** | Sonnet 4.5 | GPT-5 | Composer-1, Grok Code, Haiku 4.5 |
| **Developer** | Sonnet 4.5 | GPT-5 Codex High | Composer-1, Grok Code |

### Available Models:
- ✅ **Sonnet 4.5** (Claude 3.5 Sonnet) - Best for code, architecture, technical decisions
- ✅ **GPT-5** - Good for docs, requirements, planning
- ✅ **GPT-5 Codex High** - Specialized for code generation
- ✅ **Haiku 4.5** (Claude 3.5 Haiku) - Fast, for simple tasks only
- ❌ **Composer-1** - Not suitable for professional development
- ❌ **Grok Code** - Not suitable for professional development

### Why Sonnet 4.5 for Technical Roles?
- **Superior code quality**: Follows patterns and conventions
- **Deep reasoning**: Better at complex architectural decisions
- **Security awareness**: Careful about edge cases and vulnerabilities
- **Consistency**: Maintains code quality across large refactors
- **Testing**: Writes comprehensive test suites

### When to Use Each Model?
- **Sonnet 4.5**: Code, architecture, complex decisions, security
- **GPT-5**: Requirements, documentation, planning, review notes
- **GPT-5 Codex High**: Pure code generation, boilerplate
- **Haiku 4.5**: Simple docs, quick updates (Analyst only)
- **Composer-1, Grok Code**: Never (insufficient quality)

**Detailed guide:** See [MODELS.md](MODELS.md)

## 📊 Review Matrix

| Reviewer | Analyst 1-pager | Architect 3-pager | Tech Lead 6-pager | Developer Code |
|----------|----------------|-------------------|-------------------|----------------|
| **Analyst** | N/A | Requirements alignment | Scope, feasibility | Acceptance criteria |
| **Architect** | Constraints | N/A | Architectural compliance | Layer boundaries |
| **Tech Lead** | Feasibility | Plan alignment | N/A | CI gates, quality |
| **Developer** | Clarity | Interface clarity | Plan clarity | Peer review |

## 🚨 Escalation Paths

**Scope Change Request:**
1. Developer → Tech Lead → Analyst → Stakeholder approval

**Architecture Deviation:**
1. Developer → Tech Lead → Architect review → Decision

**Blocker:**
1. Developer → Tech Lead → (Architect/Analyst if architectural/requirements issue)

**Quality Issue:**
1. Tech Lead identifies → Developer fixes → Tech Lead validates

## 📝 Documentation Standards

### File Naming
- Requirements: `epic_XX/epic_XX.md` (1-pager)
- Architecture: `epic_XX/architecture.md` (3-pager)
- Plan: `epic_XX/implementation_plan.md` (6-pager)
- Worklogs: `epic_XX/developer/worklogs/YYYY-MM-DD.md`
- ADRs: `epic_XX/developer/decisions/ADR-NNN-title.md`

### Document Structure
**Analyst 1-pager:**
```
# Epic Title
## Problem
## Scope (Must/Should/Out of Scope)
## Success Criteria
## Constraints
```

**Architect 3-pager:**
```
# Architecture Vision
## Context & Goals
## Components & Boundaries (diagram)
## Interface Contracts
## Security Validation
## Decision Records
```

**Tech Lead 6-pager:**
```
# Implementation Plan
## Staged Breakdown (with DoD)
## Testing Strategy
## Deployment Procedures
## CI/CD Gates
## Risk Register
## Migration Strategy
```

## 🔗 Related Documents
- Project Rules: `/docs/specs/cursorrules-guide.md`
- Architecture Spec: `/docs/specs/architecture.md`
- Operations Spec: `/docs/specs/operations.md`
- System Spec: `/docs/specs/specs.md`

---

*This framework ensures clear separation of concerns and prevents scope creep across roles.*
