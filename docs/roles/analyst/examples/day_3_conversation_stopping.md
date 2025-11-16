# Day 3 Example: Conversation Stopping Conditions

## Purpose

Demonstrate how the Analyst agent recognizes when sufficient clarity is achieved and stops gathering requirements, avoiding over-questioning and information overload.

---

## Scenario

**Epic:** EP23 - Payment Processing System
**Stakeholder:** Product Owner
**Analyst Goal:** Gather payment method requirements
**Stopping Condition:** `clarity_score >= 0.80` OR `max_exchanges = 15`

---

## Full Session Transcript (Anonymized)

### Exchange 1: Initial Question

**Analyst:**
> "I'm gathering requirements for the payment processing system (EP23). Let's start with the basics:
>
> **Q1:** What payment methods must the system support?"

**Stakeholder (Product Owner):**
> "We need to support credit cards and maybe PayPal."

**Clarity Assessment:**
```json
{
  "requirement_id": "REQ-001-draft",
  "text": "Support credit cards and PayPal",
  "clarity_score": 0.45,
  "clarity_issues": [
    "Vague: 'maybe PayPal' - is it required or optional?",
    "Missing: Which credit card types? (Visa, MC, AmEx, Discover?)",
    "Missing: International cards supported?",
    "Missing: Debit cards separate from credit cards?"
  ],
  "next_action": "ask_clarifying_questions"
}
```

**Decision:** Continue gathering (clarity too low)

---

### Exchange 2: Clarifying Details

**Analyst:**
> "Thank you. Let me clarify:
>
> **Q2:** Which credit card brands specifically? (Visa, Mastercard, American Express, Discover, etc.)
> **Q3:** Should we support international credit cards?
> **Q4:** Is PayPal required for MVP or a future enhancement?"

**Stakeholder:**
> "For MVP: Visa, Mastercard, and American Express are required. International cards yes, we have customers in EU and Asia. PayPal is required too."

**Clarity Assessment:**
```json
{
  "requirement_id": "REQ-001-draft",
  "text": "Support Visa, Mastercard, American Express credit cards (international). Support PayPal.",
  "clarity_score": 0.75,
  "clarity_improvements": [
    "✅ Specific card brands identified",
    "✅ International support confirmed",
    "✅ PayPal confirmed as required"
  ],
  "remaining_issues": [
    "Missing: Debit cards?",
    "Missing: Other payment methods (Apple Pay, Google Pay, bank transfer)?",
    "Missing: Currency support?"
  ],
  "next_action": "ask_remaining_questions"
}
```

**Decision:** Continue (approaching threshold but not yet)

---

### Exchange 3: Final Details

**Analyst:**
> "Great, that's much clearer. A few more questions:
>
> **Q5:** What about debit cards separate from credit cards?
> **Q6:** Should we support digital wallets (Apple Pay, Google Pay)?
> **Q7:** Which currencies need to be supported?"

**Stakeholder:**
> "Debit cards yes, same brands as credit cards. For MVP, we'll skip Apple Pay and Google Pay - that's Phase 2. Currencies: USD, EUR, and GBP."

**Clarity Assessment:**
```json
{
  "requirement_id": "REQ-001",
  "text": "System must support credit/debit card payments (Visa, Mastercard, American Express, international). Support PayPal. Currencies: USD, EUR, GBP.",
  "clarity_score": 0.88,
  "clarity_improvements": [
    "✅ Debit cards clarified",
    "✅ Digital wallets scope defined (Phase 2, not MVP)",
    "✅ Currency support specified"
  ],
  "remaining_issues": [],
  "acceptance_criteria_draft": [
    "Visa/MC/AmEx credit and debit cards accepted",
    "International card support (EU, Asia)",
    "PayPal integration functional",
    "Multi-currency: USD, EUR, GBP"
  ],
  "next_action": "stop_gathering_move_to_next_requirement"
}
```

**Decision:** ✅ **STOP** - Clarity threshold met (0.88 >= 0.80)

---

### Exchange 4: Confirmation & Move to Next Requirement

**Analyst:**
> "Perfect! I have sufficient clarity on payment methods (clarity score: 0.88).
>
> **Summary:**
> - ✅ REQ-001: Credit/debit cards (Visa, MC, AmEx) + PayPal
> - ✅ International support
> - ✅ Currencies: USD, EUR, GBP
> - ❌ Apple Pay, Google Pay (Phase 2, out of MVP scope)
>
> **Next topic:** Let's discuss transaction security and compliance requirements.
>
> **Q8:** What security standards must we comply with? (e.g., PCI DSS?)"

**Stakeholder:**
> "Yes, PCI DSS Level 1 compliance is mandatory. We're a merchant processing over 6 million transactions per year."

**Clarity Assessment (New Requirement):**
```json
{
  "requirement_id": "REQ-002-draft",
  "text": "PCI DSS Level 1 compliance mandatory",
  "clarity_score": 0.70,
  "clarity_issues": [
    "Missing: GDPR or other data privacy requirements?",
    "Missing: Fraud detection requirements?",
    "Missing: 3D Secure support?"
  ],
  "next_action": "ask_clarifying_questions"
}
```

**Decision:** Continue on new requirement...

---

## Stopping Trigger Analysis

### Requirement REQ-001: Payment Methods

| Exchange | Clarity Score | Threshold | Decision | Reason |
|----------|--------------|-----------|----------|--------|
| 1 | 0.45 | 0.80 | Continue | Too vague ("maybe PayPal", no card types) |
| 2 | 0.75 | 0.80 | Continue | Close but missing details (debit cards, currencies) |
| 3 | 0.88 | 0.80 | **STOP** | ✅ Threshold exceeded, all details clear |

### Clarity Score Calculation

```python
def calculate_clarity_score(requirement: dict) -> float:
    """Calculate clarity score based on requirement completeness."""

    factors = {
        "specificity": 0.0,      # 0.0 = vague, 1.0 = specific
        "measurability": 0.0,    # Can we test it?
        "completeness": 0.0,     # All aspects covered?
        "consistency": 0.0,      # No contradictions?
        "acceptance_ready": 0.0  # Can we write AC?
    }

    # Exchange 1: "credit cards and maybe PayPal"
    # specificity: 0.3 (vague)
    # measurability: 0.6 (testable but incomplete)
    # completeness: 0.4 (missing details)
    # consistency: 1.0 (no contradictions yet)
    # acceptance_ready: 0.2 (can't write clear AC)
    # → Average: 0.45

    # Exchange 2: "Visa, MC, AmEx, international, PayPal required"
    # specificity: 0.8 (specific brands)
    # measurability: 0.8 (testable)
    # completeness: 0.7 (still missing currencies, debit cards)
    # consistency: 1.0 (no contradictions)
    # acceptance_ready: 0.6 (getting closer)
    # → Average: 0.75

    # Exchange 3: "Visa/MC/AmEx credit+debit, PayPal, USD/EUR/GBP"
    # specificity: 1.0 (crystal clear)
    # measurability: 1.0 (fully testable)
    # completeness: 0.9 (minor: fraud detection, 3DS not discussed)
    # consistency: 1.0 (no contradictions)
    # acceptance_ready: 0.9 (can write comprehensive AC)
    # → Average: 0.88 ✅ STOP

    return sum(factors.values()) / len(factors)
```

---

## Alternative Stopping Scenarios

### Scenario A: Max Exchanges Reached

```
Exchanges: 15
Clarity Score: 0.68 (below threshold)

→ Analyst Decision: STOP due to exchange limit
→ Output includes:
  - "Warning: Clarity threshold not met (0.68 < 0.80)"
  - "Open questions documented for follow-up"
  - "Status: incomplete - requires additional session"
```

### Scenario B: Stakeholder Signals Completion

```
Exchange 7:
Stakeholder: "That's all the information I have. Legal team needs to approve the rest."

Clarity Score: 0.72 (below threshold but external blocker)

→ Analyst Decision: STOP with conditional status
→ Output:
  - "Status: blocked - pending legal approval"
  - "Next action: Schedule follow-up after legal review"
  - "Temporary clarity: 0.72 (will improve after legal input)"
```

### Scenario C: High Clarity Reached Early

```
Exchange 2:
Clarity Score: 0.92 (exceptional clarity from start)

→ Analyst Decision: STOP early (efficiency)
→ Output:
  - "Excellent clarity achieved in 2 exchanges"
  - "Moving to next requirement area"
  - "Token savings: ~1,200 tokens (avoided 5-8 exchanges)"
```

---

## Integration Impact

### For Architect Role

**Without Stopping Condition (Over-gathering):**
```json
{
  "requirements": [
    {"text": "Support payments", "clarity": 0.45},
    // ... 10+ exchanges of back-and-forth ...
    {"text": "Maybe support cryptocurrency?", "clarity": 0.30},
    {"text": "Consider BNPL (buy now pay later)?", "clarity": 0.25}
  ],
  "exchanges": 18,
  "tokens_used": 9000,
  "architect_feedback": "Too much noise. Which requirements are actually in scope?"
}
```

**With Stopping Condition (Day 3 Pattern):**
```json
{
  "requirements": [
    {"text": "Support Visa/MC/AmEx credit+debit, PayPal. USD/EUR/GBP.", "clarity": 0.88}
  ],
  "exchanges": 3,
  "tokens_used": 1500,
  "architect_feedback": "Clear scope. Can proceed with design."
}
```

**Architect Time Saved:** 2 hours (no clarification loop needed)

---

### For Tech Lead Role

**Benefit:** Clear requirements mean clearer implementation plans
- Less time spent interpreting ambiguous requirements
- Acceptance criteria are testable (clarity >= 0.80)
- Can proceed directly to stage planning

---

## Metrics

### Session Statistics

```
Epic: EP23
Total Requirements Gathered: 8
Average Exchanges per Requirement: 3.2
Average Clarity Score: 0.86
Total Session Tokens: 6,400
Stopping Condition Triggers:
  - Clarity threshold met: 7 requirements
  - Max exchanges: 0 requirements
  - External blocker: 1 requirement (legal approval pending)

Comparison to Non-Stopping Sessions:
  - Token reduction: 42% (6.4K vs 11K average)
  - Time reduction: 35% (2 hours vs 3+ hours)
  - Architect clarification requests: 1 (vs 5 average)
```

---

## Key Takeaways

1. **Stopping Condition Prevents Over-Gathering**
   - Clear threshold (0.80) prevents endless questioning
   - Saves tokens and stakeholder time

2. **Clarity Score is Measurable**
   - Based on specificity, measurability, completeness, consistency
   - Transparent to stakeholders

3. **Multiple Stop Triggers**
   - Clarity threshold (primary)
   - Max exchanges (safety)
   - External blockers (pragmatic)

4. **Downstream Benefits**
   - Architect gets clear requirements
   - Tech Lead writes plans faster
   - Developer implements with confidence

---

## Related Documentation

- See `docs/roles/analyst/day_capabilities.md#day-3` for technique details
- See `docs/operational/context_limits.md` for token budgets
- See `docs/operational/handoff_contracts.md` for output format
