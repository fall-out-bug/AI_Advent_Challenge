"""Intent parsing orchestrator using LLM for natural language understanding.

Refactored to use extracted modules following Single Responsibility Principle.
Following the Zen of Python: Simple is better than complex.
"""

import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Tuple, runtime_checkable

from src.application.orchestration.intent_clarification import (
    IntentClarificationGenerator,
)
from src.application.orchestration.intent_fallback import IntentFallbackParser
from src.application.orchestration.intent_parser import IntentLLMParser
from src.application.orchestration.intent_validator import IntentValidator
from src.domain.entities.intent import IntentParseResult
from src.domain.exceptions.intent_exceptions import IntentParseError, LLMParseError

logger = logging.getLogger(__name__)


@dataclass
@runtime_checkable
class _SupportsGenerate(Protocol):
    """Protocol for lightweight async LLM stubs used in tests."""

    async def generate(
        self, prompt: str, temperature: float = 0.2, max_tokens: int = 512
    ) -> str:
        """Generate text from prompt."""


class IntentOrchestrator:
    """Parse natural language into structured task intent using LLM.

    Uses local LLM (Mistral/Qwen) for intent parsing with fallback to
    deterministic parser if LLM is unavailable.

    This is a thin coordinator following Dependency Inversion Principle:
    - Delegates LLM parsing to IntentLLMParser
    - Delegates fallback parsing to IntentFallbackParser
    - Delegates validation to IntentValidator
    - Delegates clarification to IntentClarificationGenerator

    Methods:
        parse_task_intent: Extract fields using LLM or fallback parser
        generate_clarification_questions: Produce questions for missing fields
        validate_intent_completeness: Check completeness and report missing info
    """

    def __init__(
        self,
        model_name: str = "mistral",
        use_llm: bool = True,
        temperature: float = 0.2,
        max_tokens: int = 512,
        llm: Optional[_SupportsGenerate] = None,
    ) -> None:
        """Initialize orchestrator.

        Args:
            model_name: LLM model name (mistral, qwen, etc.)
            use_llm: Whether to use LLM (False = deterministic parser only)
            temperature: LLM temperature for generation
            max_tokens: Maximum tokens for LLM response
        """
        self.use_llm = use_llm
        self.llm_parser: Optional[IntentLLMParser] = None
        self.fallback_parser = IntentFallbackParser()
        self.validator = IntentValidator()
        self.clarification_generator = IntentClarificationGenerator()

        if llm is not None:
            self.use_llm = True
            self.llm_parser = IntentLLMParser(
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            self.llm_parser.llm_client = None
            self.llm_parser._fallback_llm_client = llm  # type: ignore[attr-defined]
            logger.info("IntentOrchestrator initialized with injected LLM stub")
        elif self.use_llm:
            try:
                self.llm_parser = IntentLLMParser(
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                logger.info(
                    f"IntentOrchestrator initialized with LLM support: {model_name}"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize LLM parser: {e}")
                self.use_llm = False

    async def parse_task_intent(
        self, text: str, context: Optional[Dict] = None
    ) -> IntentParseResult:
        """Parse natural language task intent using LLM.

        Args:
            text: User's natural language input
            context: Optional conversation context

        Returns:
            IntentParseResult with parsed fields

        Raises:
            IntentParseError: If parsing fails completely
        """
        context = context or {}

        # Try LLM parsing first
        if self.use_llm and self.llm_parser:
            try:
                logger.debug(f"Attempting LLM parsing for text: {text[:100]}")
                result = await self.llm_parser.parse(text, context)
                if result:
                    logger.info(
                        f"LLM parsing successful: title={result.title}, deadline={result.deadline_iso}"
                    )
                    # Generate clarification questions if needed
                    if result.needs_clarification and not result.questions:
                        result.questions = (
                            self.clarification_generator.generate_questions(
                                result.title, result.deadline_iso, result.priority
                            )
                        )
                    return result
                else:
                    logger.warning("LLM parsing returned None, using fallback")
            except LLMParseError as e:
                logger.warning(f"LLM parsing failed: {e}, using fallback")
            except Exception as e:
                logger.warning(
                    f"LLM parsing failed with unexpected error: {e}, using fallback",
                    exc_info=True,
                )
        else:
            if not self.use_llm:
                logger.debug("LLM disabled, using fallback parser")
            elif not self.llm_parser:
                logger.debug("LLM parser not available, using fallback parser")

        # Fallback to deterministic parser
        logger.debug("Using fallback deterministic parser")
        try:
            result = self.fallback_parser.parse(text, context)
            # Generate clarification questions if needed
            if result.needs_clarification:
                result.questions = self.clarification_generator.generate_questions(
                    result.title, result.deadline_iso, result.priority
                )
            return result
        except Exception as e:
            raise IntentParseError(
                f"Fallback parsing failed: {e}", original_error=e
            ) from e

    def generate_clarification_questions(
        self, title: str, deadline_iso: Optional[str], priority: str
    ) -> List[str]:
        """Generate clarifying questions for missing fields.

        Args:
            title: Task title
            deadline_iso: ISO deadline or None
            priority: Priority level

        Returns:
            List of clarifying questions
        """
        return self.clarification_generator.generate_questions(
            title, deadline_iso, priority
        )

    def validate_intent_completeness(
        self, result: IntentParseResult
    ) -> Tuple[bool, List[str]]:
        """Validate intent completeness.

        Args:
            result: Intent parse result

        Returns:
            Tuple of (is_complete, missing_fields)
        """
        return self.validator.validate_completeness(result)

    async def refine_with_answers(
        self, result: IntentParseResult, answers: List[str]
    ) -> IntentParseResult:
        """Merge clarification answers back into the parse result.

        Args:
            result: Existing parse result with pending questions.
            answers: Answers provided by the user in question order.

        Returns:
            Updated IntentParseResult with merged answers.
        """
        updated = result.copy(deep=True)
        for index, answer in enumerate(answers):
            if index >= len(result.questions):
                break
            question = result.questions[index]
            key = getattr(question, "key", None) if hasattr(question, "key") else None
            if key == "deadline":
                updated.deadline_iso = answer
            elif key == "priority":
                updated.priority = answer
            elif key == "description":
                updated.description = answer
            elif key == "tags":
                try:
                    parsed = json.loads(answer)
                    if isinstance(parsed, list):
                        updated.tags = [str(tag) for tag in parsed]
                except json.JSONDecodeError:
                    updated.tags = [answer]

        updated.needs_clarification = False
        updated.questions = []
        return updated
