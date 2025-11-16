# Day 8 Example: Token Management & Context Budgeting

## Purpose

Demonstrate how the Analyst agent manages token budgets during long requirement gathering sessions, applies compression when approaching limits, and maintains conversation quality within a 12K context window.

---

## Token Budget Configuration

### Context Window: 12,000 tokens

```python
TOKEN_BUDGET = {
    "total_context": 12000,
    "system_prompts": 800,      # Fixed overhead
    "safety_margin": 2000,      # Reserve for final output
    "working_budget": 9200,     # Available for conversation
    "compression_trigger": 7000 # Trigger at 70% of working budget
}
```

### Token Allocation Strategy

```
┌─────────────────────────────────────────┐
│ 12K Total Context Window                │
├─────────────────────────────────────────┤
│ System Prompts: 800 tokens (6.7%)       │ ← Fixed
├─────────────────────────────────────────┤
│ Conversation History: 1,500 tokens      │ ← Compressed (Day 15)
│ (after compression from 7,500)          │
├─────────────────────────────────────────┤
│ Active Gathering: 6,000 tokens          │ ← Working buffer
├─────────────────────────────────────────┤
│ Final JSON Output: 2,000 tokens         │ ← Reserved
├─────────────────────────────────────────┤
│ Safety Margin: 1,700 tokens             │ ← Overflow protection
└─────────────────────────────────────────┘
```

---

## Scenario: Complex Epic with Long Session

**Epic:** EP24 - Multi-Tenant SaaS Platform  
**Complexity:** High (multiple modules, integrations, security)  
**Expected Exchanges:** 25-30  
**Session Goal:** Gather comprehensive requirements across 5 modules

---

## Session Tracking (Real-Time Token Monitoring)

### Exchanges 1-5: Authentication Module

```
Exchange 1 (Token Count: 450)
├─ User input: 120 tokens
├─ Analyst response: 280 tokens
└─ Running total: 800 (system) + 450 = 1,250 tokens (10% used)

Exchange 2 (Token Count: 520)
├─ User input: 180 tokens
├─ Analyst response: 340 tokens
└─ Running total: 1,250 + 520 = 1,770 tokens (15% used)

Exchange 3 (Token Count: 480)
├─ User input: 150 tokens
├─ Analyst response: 330 tokens
└─ Running total: 1,770 + 480 = 2,250 tokens (19% used)

Exchange 4 (Token Count: 510)
├─ User input: 160 tokens
├─ Analyst response: 350 tokens
└─ Running total: 2,250 + 510 = 2,760 tokens (23% used)

Exchange 5 (Token Count: 490)
├─ User input: 140 tokens
├─ Analyst response: 350 tokens
└─ Running total: 2,760 + 490 = 3,250 tokens (27% used)

Status: ✅ Within budget, continue gathering
```

---

### Exchanges 6-10: Billing Module

```
Exchange 6 (Token Count: 530)
└─ Running total: 3,250 + 530 = 3,780 tokens (32% used)

Exchange 7 (Token Count: 560)
└─ Running total: 3,780 + 560 = 4,340 tokens (36% used)

Exchange 8 (Token Count: 495)
└─ Running total: 4,340 + 495 = 4,835 tokens (40% used)

Exchange 9 (Token Count: 520)
└─ Running total: 4,835 + 520 = 5,355 tokens (45% used)

Exchange 10 (Token Count: 540)
└─ Running total: 5,355 + 540 = 5,895 tokens (49% used)

Status: ✅ Still healthy, monitoring closely
```

---

### Exchanges 11-15: Integration Module

```
Exchange 11 (Token Count: 580)
└─ Running total: 5,895 + 580 = 6,475 tokens (54% used)

Exchange 12 (Token Count: 550)
└─ Running total: 6,475 + 550 = 7,025 tokens (59% used)

⚠️  WARNING: Approaching compression trigger (7,000 tokens)

Exchange 13 (Token Count: 610)
└─ Running total: 7,025 + 610 = 7,635 tokens (64% used)

🔴 TRIGGER: Token budget at 64% → Initiate compression

Exchange 14 (Token Count: 520)
└─ Running total: 7,635 + 520 = 8,155 tokens (68% used)

Exchange 15 (Token Count: 490)
└─ Running total: 8,155 + 490 = 8,645 tokens (72% used)

Status: 🔴 COMPRESSION REQUIRED IMMEDIATELY
```

---

## Compression Event (After Exchange 15)

### Before Compression

```
Conversation History: 8,645 tokens
├─ Authentication Module: 2,450 tokens (Exchanges 1-5)
├─ Billing Module: 2,645 tokens (Exchanges 6-10)
├─ Integration Module: 2,750 tokens (Exchanges 11-15)
└─ System prompts: 800 tokens

Total: 9,445 tokens (79% of 12K window)
Remaining: 2,555 tokens (21%)

Risk: Only ~4-5 more exchanges possible before overflow
```

### Analyst Decision

**Analyst (Internal Log):**
> "Token budget critical: 9,445/12,000 used (79%).
> 
> **Action:** Apply Day 15 compression pattern
> - Target: 80% reduction on exchanges 1-15
> - Preserve: Requirements, clarity scores, decisions, open questions
> - Discard: Conversational filler, timestamps, redundant details
> 
> **Expected result:** 8,645 → ~1,700 tokens
> **Token freed:** ~6,900 tokens
> **New remaining:** ~9,400 tokens (78% available)"

---

### Compression Execution (Day 15 Pattern)

```python
def compress_conversation_history(exchanges: list) -> str:
    """Compress conversation using map-reduce pattern."""
    
    # Map: Group by topic/module
    topics = {
        "authentication": exchanges[0:5],   # 2,450 tokens
        "billing": exchanges[5:10],         # 2,645 tokens
        "integration": exchanges[10:15]     # 2,750 tokens
    }
    
    # Reduce: Summarize each topic
    summaries = []
    for topic, topic_exchanges in topics.items():
        summary = extract_core_info(topic_exchanges)
        summaries.append(summary)
    
    # Merge: Create compressed context
    compressed = merge_summaries(summaries)
    
    return compressed  # ~1,700 tokens (80% reduction)
```

---

### After Compression

**Compressed Conversation Context (1,729 tokens):**

```markdown
# COMPRESSED CONTEXT (Exchanges 1-15)

## Module 1: Authentication (Clarity: 0.88)

### Requirements
- REQ-AUTH-001: OAuth2 + SAML SSO support
  - AC: Google, Microsoft, Okta providers
  - AC: SAML 2.0 for enterprise customers
- REQ-AUTH-002: Multi-factor authentication
  - AC: SMS, TOTP, email options
  - AC: Admin-configurable MFA policies
- REQ-AUTH-003: Session management
  - AC: JWT tokens, 24h expiry
  - AC: Refresh token rotation

### Decisions
- ✅ Use Auth0 for OAuth (approved by CTO)
- ✅ Store sessions in Redis (24h TTL)
- ❌ Biometric auth out of MVP scope

### Open Questions
- None (module complete)

---

## Module 2: Billing (Clarity: 0.82)

### Requirements
- REQ-BILL-001: Multi-tier subscription plans
  - AC: Free, Pro, Enterprise tiers
  - AC: Annual/monthly billing cycles
- REQ-BILL-002: Payment processing
  - AC: Stripe integration (primary)
  - AC: Invoice generation (PDF)
- REQ-BILL-003: Usage-based billing
  - AC: Track API calls, storage, compute
  - AC: Monthly aggregation and invoicing

### Decisions
- ✅ Stripe as payment provider
- ✅ Generate invoices via Stripe API
- ❌ Crypto payments out of scope

### Open Questions
- Tax handling for international customers? (pending CFO input)

---

## Module 3: Integration (Clarity: 0.79)

### Requirements
- REQ-INT-001: REST API for third-party integrations
  - AC: OpenAPI 3.0 spec
  - AC: API key authentication
- REQ-INT-002: Webhooks for event notifications
  - AC: Configurable endpoints per customer
  - AC: Retry logic (3 attempts)
- REQ-INT-003: Rate limiting
  - AC: 1000 req/min per API key
  - AC: 429 responses with Retry-After header

### Decisions
- ✅ Use FastAPI for REST endpoints
- ✅ Redis for rate limiting counters

### Open Questions
- Webhook authentication mechanism? (HMAC signature?)
- GraphQL API needed? (stakeholder unclear)

---

## Session Metadata
- Exchanges compressed: 15
- Original tokens: 8,645
- Compressed tokens: 1,729
- Compression ratio: 80%
- Information retention: 94% (measured by clarity alignment)
- Modules remaining: 2 (Reporting, Analytics)
```

---

### Token Budget After Compression

```
NEW Token Allocation:
├─ System prompts: 800 tokens
├─ Compressed history (Ex 1-15): 1,729 tokens
├─ Reserved for output: 2,000 tokens
├─ Safety margin: 1,700 tokens
└─ Available for continued gathering: 5,771 tokens

Total accounted: 6,229 tokens (52% of window)
Remaining budget: 5,771 tokens (48% of window)

→ Can continue for ~10-12 more exchanges before next compression
```

---

## Exchanges 16-25: Reporting & Analytics (Post-Compression)

```
Exchange 16 (Token Count: 490)
└─ Running total: 800 + 1,729 + 490 = 3,019 tokens (25% used)

Exchange 17 (Token Count: 520)
└─ Running total: 3,019 + 520 = 3,539 tokens (29% used)

Exchange 18 (Token Count: 505)
└─ Running total: 3,539 + 505 = 4,044 tokens (34% used)

...

Exchange 25 (Token Count: 480)
└─ Running total: 7,890 tokens (66% used)

Status: ✅ Completed all 5 modules within budget
Final compressed context: 2,100 tokens (for handoff)
```

---

## Final Session Summary

### Token Usage Statistics

```
═══════════════════════════════════════════════════════
                  TOKEN BUDGET REPORT
               Epic EP24 - Requirements Session
═══════════════════════════════════════════════════════

Total Exchanges:              25
Total Session Duration:       3.5 hours

TOKEN BREAKDOWN:
├─ Original conversation:     12,450 tokens (if uncompressed)
├─ After compression (Ex 15): 1,729 tokens (8,645 → 1,729)
├─ Exchanges 16-25:          4,870 tokens
├─ Final compressed output:   2,100 tokens
└─ Peak usage:               8,699 tokens (72% of 12K window)

COMPRESSION EVENTS:
├─ Compression #1 (Ex 15):   8,645 → 1,729 tokens (80% reduction)
└─ Total token savings:      6,916 tokens

EFFICIENCY METRICS:
├─ Without compression:      12,450 tokens (overflow ❌)
├─ With Day 8 management:    8,699 tokens (within budget ✅)
├─ Token savings:            30% (via compression)
└─ Session completion:       100% (all 5 modules gathered)

QUALITY METRICS:
├─ Average clarity score:    0.84 (high quality)
├─ Information retention:    94% (post-compression)
├─ Architect clarifications: 0 (no follow-up needed)
└─ Total requirements:       18 (across 5 modules)

═══════════════════════════════════════════════════════
```

---

## Alternative Scenarios

### Scenario A: No Token Management (Overflow)

```
❌ Without Day 8 Pattern:

Exchange 1-15:   8,645 tokens
Exchange 16-25:  4,870 tokens
System prompts:  800 tokens
Total:           14,315 tokens

Result: 14,315 > 12,000 (OVERFLOW at Exchange 21)
└─ Context window exceeded
└─ Conversation truncated (lost early requirements)
└─ Must restart session (wasted 2+ hours)
```

### Scenario B: Aggressive Compression (Too Early)

```
⚠️  Compression at Exchange 5 (too early):

Token usage: 3,250 tokens (27% of window)
Compression: 2,450 → 490 tokens

Issue: Premature compression wastes compute
- Compression costs ~500 tokens (LLM summary call)
- Net savings: 2,450 - 490 - 500 = 1,460 tokens
- But only 27% used → unnecessary

Recommendation: Wait until 60-70% threshold
```

### Scenario C: Multiple Compression Events

```
✅ Large Epic (50+ exchanges):

Compression #1 (Ex 20): 9,800 → 1,960 tokens (80% reduction)
├─ Continue gathering...
Compression #2 (Ex 40): 9,200 → 1,840 tokens (80% reduction)
├─ Continue gathering...
Final output (Ex 50): 2,500 tokens

Total compressions: 2
Session completed: Yes
Quality maintained: 92% information retention
```

---

## Integration with Day 15 (Compression)

### Compression Quality Validation

```python
def validate_compression_quality(
    original: ConversationHistory,
    compressed: CompressedSummary
) -> CompressionQuality:
    """Ensure compression preserves critical information."""
    
    quality_checks = {
        "requirements_preserved": check_all_requirements_present(
            original, compressed
        ),
        "decisions_preserved": check_all_decisions_present(
            original, compressed
        ),
        "clarity_alignment": compare_clarity_scores(
            original, compressed
        ),
        "open_questions_preserved": check_questions_present(
            original, compressed
        )
    }
    
    return CompressionQuality(
        passed=all(quality_checks.values()),
        checks=quality_checks,
        information_retention=calculate_retention(original, compressed)
    )

# Example result:
# {
#   "passed": True,
#   "checks": {
#     "requirements_preserved": True,    # 18/18 requirements
#     "decisions_preserved": True,       # 12/12 decisions
#     "clarity_alignment": 0.94,         # 94% alignment
#     "open_questions_preserved": True   # 4/4 questions
#   },
#   "information_retention": 0.94
# }
```

---

## Monitoring & Alerts

### Real-Time Token Monitoring Dashboard

```
┌──────────────────────────────────────────────────────────┐
│ ANALYST TOKEN BUDGET MONITOR - EP24                      │
├──────────────────────────────────────────────────────────┤
│ Context Window: 12,000 tokens                            │
│                                                          │
│ Current Usage: 8,699 / 12,000 (72%)                     │
│ ████████████████████████████████░░░░░░░░░░               │
│                                                          │
│ Breakdown:                                               │
│ ├─ System prompts:     800 (7%)  [Fixed]                │
│ ├─ Compressed history: 1,729 (14%) [Optimized]          │
│ ├─ Active gathering:   4,870 (41%) [In progress]        │
│ ├─ Reserved output:    2,000 (17%) [Reserved]           │
│ └─ Safety margin:      1,700 (14%) [Buffer]             │
│                                                          │
│ Alerts:                                                  │
│ ✅ Within budget (72% < 80% threshold)                   │
│ ✅ Compression applied successfully at Ex 15             │
│ ✅ Can continue for ~8 more exchanges                    │
│                                                          │
│ Compression History:                                     │
│ └─ Event #1 (Ex 15): 8,645 → 1,729 tokens (-80%)        │
│                                                          │
│ Session Stats:                                           │
│ ├─ Exchanges: 20 / ~30 estimated                        │
│ ├─ Requirements: 14 / 18 target                         │
│ ├─ Avg clarity: 0.84                                    │
│ └─ ETA: 1.2 hours remaining                             │
└──────────────────────────────────────────────────────────┘
```

---

## Best Practices (Day 8 Patterns)

### 1. Track Tokens Proactively

```python
class TokenBudgetTracker:
    def __init__(self, context_window: int = 12000):
        self.context_window = context_window
        self.system_prompts = 800
        self.safety_margin = 2000
        self.compression_threshold = 0.70  # 70% of working budget
        
        self.working_budget = (
            context_window - system_prompts - safety_margin
        )  # 9,200 tokens
        
        self.current_usage = system_prompts
        self.compression_events = []
    
    def should_compress(self) -> bool:
        """Check if compression should be triggered."""
        usage_ratio = self.current_usage / self.context_window
        return usage_ratio >= self.compression_threshold
    
    def remaining_exchanges_estimate(self) -> int:
        """Estimate how many exchanges before compression needed."""
        avg_tokens_per_exchange = 500
        remaining_tokens = (
            self.working_budget - (self.current_usage - self.system_prompts)
        )
        return remaining_tokens // avg_tokens_per_exchange
```

### 2. Compress at Right Time

- ✅ Compress at 60-70% working budget usage
- ❌ Don't compress too early (wastes compute)
- ❌ Don't wait until 90%+ (risk of overflow)

### 3. Validate Compression Quality

- Check requirements preserved: 100%
- Check decisions preserved: 100%
- Clarity alignment: ≥90%
- Open questions preserved: 100%

### 4. Reserve Tokens for Output

- Always reserve 2,000 tokens for final JSON output
- Safety margin: 1,700 tokens for unexpected overhead

---

## Impact on Downstream Roles

### For Architect

**Benefit:** Receives complete, compressed requirements without token bloat
- Input tokens: 2,100 (compressed)
- Architect available budget: 9,900 tokens (for design work)
- No need to re-query Analyst (all context provided)

### For Tech Lead

**Benefit:** Implementation plan can reference full requirement context
- Clear traceability: REQ-AUTH-001 → Design → Plan → Implementation
- No lost context from token overflow

---

## Key Takeaways

1. **Token Management Enables Long Sessions**
   - 25-exchange session possible within 12K window
   - Without compression: Overflow at ~21 exchanges

2. **Compression is Critical (Day 15 Dependency)**
   - 80% token reduction while preserving 94% information
   - Enables 2-3x more exchanges per session

3. **Proactive Monitoring Prevents Overflow**
   - Track usage in real-time
   - Trigger compression at 70% threshold
   - Never exceed 85% to maintain safety margin

4. **Quality Maintained Through Compression**
   - Clarity score: 0.84 (before) → 0.82 (after compression)
   - All requirements, decisions, open questions preserved

5. **Downstream Benefits**
   - Architect gets complete context in compressed form
   - Tech Lead has full traceability
   - No lost information from truncation

---

## Related Documentation

- See `docs/roles/analyst/day_capabilities.md#day-8` for technique details
- See `docs/roles/analyst/day_capabilities.md#day-15` for compression pattern
- See `docs/operational/context_limits.md` for budget configuration
- See `docs/operational/handoff_contracts.md` for output format

