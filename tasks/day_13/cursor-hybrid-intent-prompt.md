# Cursor Prompt: Hybrid Intent Recognition Architecture

**Use this as a prompt to give to Cursor for implementing hybrid (rules + LLM) intent recognition**

---

## 📌 Prompt for Cursor (Copy & Paste)

```
Implement hybrid intent recognition system for Telegram Butler Agent.

Requirements:
1. Two-layer architecture:
   - Layer 1: Fast rule-based intent extraction (regex, keywords, templates)
   - Layer 2: LLM fallback (Mistral-7B for complex/ambiguous cases)

2. File structure:
   - src/domain/intent/
     - intent_classifier.py (abstract base)
     - rule_based_classifier.py (static rules, regex patterns)
     - llm_classifier.py (calls Mistral-7B API)
     - hybrid_classifier.py (orchestrates both layers)

   - src/domain/intent/rules/
     - task_rules.py (patterns for task creation/management)
     - data_rules.py (patterns for digest, statistics requests)
     - reminder_rules.py (patterns for reminder queries)
     - general_rules.py (fallback patterns)

3. Implementation details:

   a) Rule-based classifier:
      - Use regex patterns with confidence scores
      - Return (intent, confidence, extracted_entities) tuple
      - Support Russian language patterns
      - Examples:
        * "создай" / "добавь" / "напомни" → TASK_CREATE
        * "что в каналах" / "дайджест" → DATA_DIGEST
        * "мои напоминания" / "ближайшие" → REMINDERS_LIST

   b) LLM classifier (fallback):
      - Call Mistral-7B via your existing mistral_client
      - System prompt: "You are intent classifier. Return one intent type."
      - Timeout: 5 seconds
      - On LLM failure: return DEFAULT intent + log error

   c) Hybrid orchestrator:
      - Try rule-based first
      - If confidence < 0.7 OR no match → fallback to LLM
      - Log which path was used (rules vs LLM)
      - Cache recent LLM results (5 min TTL) to save API calls

4. Testing:
   - Unit tests: test each rule individually
   - Integration tests: test hybrid with mock LLM
   - Test Russian language edge cases
   - Test performance: rules should respond <100ms, LLM <5s

5. Logging:
   - Log intent path (rule/llm), confidence, extracted entities
   - Track fallback frequency (if >30% → tune rules)
   - Include in dialogue context for debugging

6. Code style:
   - Follow Python Zen: explicit > implicit
   - Type hints everywhere
   - Docstrings for each classifier method
   - No hardcoded patterns; load from config
   - SOLID principles: each classifier = single responsibility

7. Integration:
   - Fit into existing butler_orchestrator.py
   - Replace current static intent classification
   - Use existing mistral_client for LLM calls
   - Store results in dialogue_context (MongoDB)

Expected behavior:
- User: "Создай задачу купить молоко"
  → Rule matches (confidence: 0.95) → Task.CREATE intent ✓ (fast, <100ms)

- User: "Напомни мне про встречу потом"
  → Rule matches partially (confidence: 0.65) → LLM fallback → Reminder.SET intent ✓ (~3s)

- User: "Как там успехи в универе?"
  → No rule match → LLM fallback → General.CHAT intent ✓ (~3s)

Optimize for:
- Fast responses (rules first)
- Accurate classification (fallback to LLM)
- Maintainability (config-driven rules)
- Observability (logging all decisions)
```

---

## 🎯 For Your Cursor IDE

**Step 1:** Open Cursor
**Step 2:** Create new file `src/domain/intent/hybrid_classifier.py`
**Step 3:** Paste the prompt above into Cursor chat
**Step 4:** Say "Implement this architecture"

Cursor will generate the complete hybrid intent system following all your `.cursorrules` (Chief Architect, Python Zen Writer, etc.)

---

## 📊 Architecture Diagram

```
User Input (Telegram)
        ↓
┌──────────────────────────────────┐
│ HybridIntentClassifier           │
│                                  │
│ 1. Try RuleBasedClassifier       │
│    ├─ Regex patterns             │
│    ├─ Keyword matching           │
│    └─ Template matching          │
│    Result: (intent, confidence)  │
│                                  │
│ 2. Check confidence threshold    │
│    If confidence >= 0.7:         │
│    └─ Return rule_intent ✓       │
│    Else:                         │
│    └─ Call LLMClassifier         │
│                                  │
│ 3. LLMClassifier (fallback)      │
│    ├─ Call Mistral-7B            │
│    ├─ Parse LLM response         │
│    └─ Return llm_intent ✓        │
│                                  │
│ 4. Log & cache result            │
│    ├─ Track rule/llm frequency   │
│    ├─ Cache LLM results (5 min)  │
│    └─ Update metrics             │
└──────────────────────────────────┘
        ↓
IntentOrchestrator delegates to handler
```

---

## 💻 Minimal Code Example

```python
# src/domain/intent/hybrid_classifier.py

from typing import Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Supported intents."""
    TASK_CREATE = "task.create"
    TASK_LIST = "task.list"
    DATA_DIGEST = "data.digest"
    DATA_STATS = "data.stats"
    REMINDER_SET = "reminder.set"
    REMINDER_LIST = "reminder.list"
    GENERAL_CHAT = "general.chat"

class IntentResult:
    """Result of intent classification."""
    def __init__(
        self,
        intent: IntentType,
        confidence: float,
        source: str,  # "rule" or "llm"
        entities: dict = None,
    ):
        self.intent = intent
        self.confidence = confidence
        self.source = source
        self.entities = entities or {}

class HybridIntentClassifier:
    """Two-layer intent classifier: rules first, LLM fallback."""

    def __init__(
        self,
        rule_classifier,
        llm_classifier,
        confidence_threshold: float = 0.7,
    ):
        self.rule_classifier = rule_classifier
        self.llm_classifier = llm_classifier
        self.confidence_threshold = confidence_threshold

    async def classify(self, user_input: str) -> IntentResult:
        """Classify user intent (hybrid approach)."""

        # Layer 1: Try rules
        rule_result = self.rule_classifier.classify(user_input)

        if rule_result and rule_result.confidence >= self.confidence_threshold:
            logger.info(
                f"Intent recognized by rules: {rule_result.intent} "
                f"(confidence: {rule_result.confidence:.2f})"
            )
            return rule_result

        # Layer 2: Fallback to LLM
        logger.info(
            f"Rule confidence too low ({rule_result.confidence:.2f} < {self.confidence_threshold}). "
            f"Falling back to LLM..."
        )

        llm_result = await self.llm_classifier.classify(user_input)
        logger.info(f"Intent recognized by LLM: {llm_result.intent}")

        return llm_result
```

---

## 📋 Rule Patterns Example

```python
# src/domain/intent/rules/task_rules.py

TASK_CREATE_PATTERNS = [
    (r"(создай|добавь|напоминаю) .+ (задач|заметк|дел)", "TASK_CREATE", 0.95),
    (r"(нужно|надо) .+", "TASK_CREATE", 0.70),
    (r"(запомни|сохрани) .+", "TASK_CREATE", 0.85),
]

TASK_LIST_PATTERNS = [
    (r"(какие|мои) .*(задач|дел|заметок)", "TASK_LIST", 0.90),
    (r"что мне делать", "TASK_LIST", 0.85),
    (r"покажи (список|дела|задачи)", "TASK_LIST", 0.95),
]

REMINDER_PATTERNS = [
    (r"напомни мне .+", "REMINDER_SET", 0.95),
    (r"когда мне .+", "REMINDER_LIST", 0.80),
]

DATA_DIGEST_PATTERNS = [
    (r"что.*(в каналах|новое)", "DATA_DIGEST", 0.95),
    (r"(дайджест|последнее) .+", "DATA_DIGEST", 0.90),
]
```

---

## ✅ Integration with Your Existing Code

After Cursor generates the hybrid classifier:

```python
# In your butler_orchestrator.py

from src.domain.intent.hybrid_classifier import HybridIntentClassifier
from src.domain.intent.rule_based_classifier import RuleBasedClassifier
from src.domain.intent.llm_classifier import LLMClassifier

class ButtlerOrchestrator:
    def __init__(self, mistral_client, mcp_client, mongodb):
        # Existing init...

        # NEW: Add hybrid intent classifier
        rule_classifier = RuleBasedClassifier()
        llm_classifier = LLMClassifier(mistral_client)

        self.intent_classifier = HybridIntentClassifier(
            rule_classifier=rule_classifier,
            llm_classifier=llm_classifier,
            confidence_threshold=0.7,
        )

    async def handle_user_message(self, user_id, message, session_id):
        # Classify intent (hybrid)
        intent_result = await self.intent_classifier.classify(message)

        # Log for debugging
        logger.info(
            f"User {user_id} intent: {intent_result.intent} "
            f"(source: {intent_result.source}, confidence: {intent_result.confidence:.2f})"
        )

        # Delegate to handler based on intent
        if intent_result.intent == IntentType.TASK_CREATE:
            return await self._handle_task_flow(user_id, message, session_id)
        elif intent_result.intent == IntentType.DATA_DIGEST:
            return await self._handle_data_flow(user_id, message, session_id)
        # ... etc
```

---

## 🧪 Test Example

```python
# tests/unit/test_hybrid_classifier.py

import pytest
from src.domain.intent.hybrid_classifier import HybridIntentClassifier, IntentType

@pytest.fixture
def mock_classifiers(mocker):
    rule_classifier = mocker.MagicMock()
    llm_classifier = mocker.AsyncMock()
    return rule_classifier, llm_classifier

@pytest.mark.asyncio
async def test_rule_based_high_confidence(mock_classifiers):
    """Rule-based classifier returns high confidence → use rules."""
    rule_classifier, llm_classifier = mock_classifiers

    # Mock rule result
    rule_result = mocker.MagicMock()
    rule_result.intent = IntentType.TASK_CREATE
    rule_result.confidence = 0.95
    rule_classifier.classify.return_value = rule_result

    classifier = HybridIntentClassifier(rule_classifier, llm_classifier)
    result = await classifier.classify("Создай задачу")

    assert result.intent == IntentType.TASK_CREATE
    assert result.source == "rule"
    llm_classifier.classify.assert_not_called()  # LLM not called

@pytest.mark.asyncio
async def test_llm_fallback_low_confidence(mock_classifiers):
    """Rule-based low confidence → fallback to LLM."""
    rule_classifier, llm_classifier = mock_classifiers

    # Mock low-confidence rule
    rule_result = mocker.MagicMock()
    rule_result.confidence = 0.5
    rule_classifier.classify.return_value = rule_result

    # Mock LLM result
    llm_result = mocker.MagicMock()
    llm_result.intent = IntentType.GENERAL_CHAT
    llm_classifier.classify.return_value = llm_result

    classifier = HybridIntentClassifier(rule_classifier, llm_classifier)
    result = await classifier.classify("Как дела?")

    assert result.intent == IntentType.GENERAL_CHAT
    assert result.source == "llm"
    llm_classifier.classify.assert_called_once()
```

---

## 🚀 How to Use This

1. **Copy the prompt** (first section) into your Cursor chat
2. **Cursor generates** the complete hybrid classifier implementation
3. **Review the code** — all `.cursorrules` applied automatically
4. **Integrate** into your `butler_orchestrator.py`
5. **Test** with your test suite
6. **Optimize** rule patterns based on real usage logs

---

## 📈 Monitoring & Tuning

After deployment, track:

```python
# Log metrics
metrics = {
    "total_classifications": 1000,
    "rule_based_count": 700,  # 70%
    "llm_fallback_count": 300,  # 30%
    "avg_rule_latency_ms": 45,
    "avg_llm_latency_ms": 2800,
}

# If LLM fallback > 40% → tune rule patterns
# If rule_latency > 200ms → optimize regex
# If llm_latency > 5s → add caching or reduce context
```

---

**Ready to generate! 🚀**

Give this prompt to Cursor and it will implement the complete hybrid intent recognition system.
