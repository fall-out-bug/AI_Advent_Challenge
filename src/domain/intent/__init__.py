"""Intent classification domain module.

Hybrid intent recognition system (rules + LLM) for user message processing.
Following Python Zen: Explicit is better than implicit.
"""

from src.domain.intent.hybrid_classifier import HybridIntentClassifier
from src.domain.intent.intent_classifier import (
    IntentClassifierProtocol,
    IntentResult,
    IntentType,
)
from src.domain.intent.llm_classifier import LLMClassifier
from src.domain.intent.rule_based_classifier import RuleBasedClassifier

__all__ = [
    "IntentClassifierProtocol",
    "IntentResult",
    "IntentType",
    "HybridIntentClassifier",
    "RuleBasedClassifier",
    "LLMClassifier",
]
