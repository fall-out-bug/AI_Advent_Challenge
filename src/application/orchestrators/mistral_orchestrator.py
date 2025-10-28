"""Mistral orchestrator for chat-based multi-step workflows.

Following Clean Architecture and the Zen of Python:
- Simple is better than complex
- Readability counts
- Functions should be ≤15 lines
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from src.application.services.context_manager import ContextManager
from src.application.services.plan_optimizer import ExecutionOptimizer
from src.domain.entities.conversation import Conversation, ExecutionPlan, ExecutionStep, IntentAnalysis
from src.domain.repositories.conversation_repository import ConversationRepository
from src.application.orchestrators.prompts import INTENT_PARSING_PROMPT, PLAN_GENERATION_PROMPT, CLARIFICATION_PROMPT
from src.application.orchestrators.response_formatters import (
    format_code_response,
    format_test_response,
    format_review_response,
    format_complexity_response
)

logger = logging.getLogger(__name__)


class MistralChatOrchestrator:
    """Orchestrator managing conversation flow with Mistral."""

    def __init__(
        self,
        unified_client: Any,
        conversation_repo: ConversationRepository,
        model_name: str = "mistral",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        confidence_threshold: float = 0.7,
        max_clarifying_questions: int = 3,
        conversation_memory_size: int = 10,
        timeout_seconds: int = 60,
        mcp_wrapper: Optional[Any] = None,
        enable_optimization: bool = True,
        enable_context_management: bool = True,
    ):
        """Initialize orchestrator.

        Args:
            unified_client: UnifiedModelClient instance
            conversation_repo: Conversation repository
            model_name: Model name for inference
            temperature: Generation temperature
            max_tokens: Maximum tokens per request
            confidence_threshold: Confidence threshold for clarification
            max_clarifying_questions: Max clarifying questions
            conversation_memory_size: Conversation memory window
            timeout_seconds: Request timeout
            mcp_wrapper: Optional MCP wrapper for tool execution
            enable_optimization: Enable plan optimization
            enable_context_management: Enable context window management
        """
        self.unified_client = unified_client
        self.conversation_repo = conversation_repo
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.confidence_threshold = confidence_threshold
        self.max_clarifying_questions = max_clarifying_questions
        self.conversation_memory_size = conversation_memory_size
        self.timeout_seconds = timeout_seconds
        self.model_available = False
        self.mcp_wrapper = mcp_wrapper
        self.enable_optimization = enable_optimization
        self.plan_optimizer = ExecutionOptimizer() if enable_optimization else None
        self.context_manager = ContextManager(max_tokens=max_tokens) if enable_context_management else None

    async def initialize(self) -> None:
        """Setup and validate model availability."""
        try:
            response = await self.unified_client.check_availability(self.model_name)
            self.model_available = response
            logger.info(f"Model {self.model_name} availability: {self.model_available}")
        except Exception as e:
            logger.warning(f"Could not check model availability: {e}")
            self.model_available = True  # Assume available if check fails

    async def handle_message(self, message: str, conversation_id: str) -> str:
        """Main entry point for handling user messages.

        Args:
            message: User message
            conversation_id: Conversation identifier

        Returns:
            Response string
        """
        conversation = await self._ensure_conversation(conversation_id)
        conversation.add_message("user", message)
        await self.conversation_repo.save(conversation)

        history = await self.conversation_repo.get_recent_messages(
            conversation_id, self.conversation_memory_size
        )

        intent = await self._parse_intent(message, history)

        if await self._check_clarification_needed(intent):
            questions = await self._generate_clarifying_questions(intent)
            return questions

        plan = await self._generate_execution_plan(intent, {}, history)

        if self.mcp_wrapper and len(plan.steps) > 0:
            results = await self.mcp_wrapper.execute_plan(plan, conversation_id)
        else:
            results = []

        response = await self._format_response(results, intent)

        conversation.add_message("assistant", response)
        await self.conversation_repo.save(conversation)

        return response

    def _build_history_context(self, history: List[dict]) -> str:
        """Build conversation history context.

        Args:
            history: Conversation history

        Returns:
            Formatted history text
        """
        if self.context_manager:
            return self.context_manager.get_context_window(history)
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])

    async def _parse_intent(self, message: str, history: List[dict]) -> IntentAnalysis:
        """Parse user intent using Mistral.

        Args:
            message: User message
            history: Conversation history

        Returns:
            Intent analysis result
        """
        history_text = self._build_history_context(history)
        context_text = f"\n\nRecent conversation:\n{history_text}\n" if history_text.strip() else ""
        prompt = INTENT_PARSING_PROMPT.format(message=message, context_text=context_text)
        response = await self._call_model(prompt)
        return self._parse_intent_json(response)

    def _parse_intent_json(self, response: str) -> IntentAnalysis:
        """Parse intent from JSON response.

        Args:
            response: JSON response string

        Returns:
            Intent analysis
        """
        try:
            data = json.loads(response)
            return IntentAnalysis(
                primary_goal=data.get("primary_goal", ""),
                tools_needed=data.get("tools_needed", []),
                parameters=data.get("parameters", {}),
                confidence=data.get("confidence", 0.5),
                needs_clarification=data.get("needs_clarification", False),
                unclear_aspects=data.get("unclear_aspects", []),
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse intent: {e}")
            return IntentAnalysis(
                primary_goal=response,
                confidence=0.5,
                needs_clarification=True,
                unclear_aspects=["Unable to parse intent"],
            )

    async def _check_clarification_needed(self, intent: IntentAnalysis) -> bool:
        """Check if clarification is needed.

        Args:
            intent: Intent analysis

        Returns:
            Whether clarification is needed
        """
        return intent.confidence < self.confidence_threshold or intent.needs_clarification

    async def _generate_clarifying_questions(self, intent: IntentAnalysis) -> str:
        """Generate clarifying questions.

        Args:
            intent: Intent analysis

        Returns:
            Questions string
        """
        unclear = ", ".join(intent.unclear_aspects)
        prompt = CLARIFICATION_PROMPT.format(unclear_aspects=unclear)
        return await self._call_model(prompt)

    async def _generate_execution_plan(  # noqa: ARG002
        self, intent: IntentAnalysis, tools: Dict[str, Any], history: List[dict] = None
    ) -> ExecutionPlan:
        """Generate execution plan.

        Args:
            intent: Intent analysis
            tools: Available tools
            history: Conversation history

        Returns:
            Execution plan
        """
        # If no tools needed, return empty plan
        if not intent.tools_needed:
            logger.info("No tools needed, returning empty plan")
            return ExecutionPlan(steps=[], estimated_time=0.0)
        
        history_text = self._build_history_context(history) if history else ""
        context_part = ""
        if history_text:
            context_text_safe = history_text.replace("```", "'''").replace("\\", "\\\\").replace('"', "'")
            context_part = f"\n\nRecent conversation:\n{context_text_safe}\n"
        
        prompt = PLAN_GENERATION_PROMPT.format(primary_goal=intent.primary_goal, context_part=context_part)
        response = await self._call_model(prompt)
        steps = self._parse_plan_json(response)
        plan = ExecutionPlan(steps=steps, estimated_time=len(steps) * 10.0)
        
        # Optimize plan if enabled
        if self.plan_optimizer:
            plan = self.plan_optimizer.optimize(plan)
        
        return plan

    def _parse_plan_json(self, response: str) -> List[ExecutionStep]:
        """Parse execution plan from JSON.

        Args:
            response: JSON response

        Returns:
            List of execution steps
        """
        try:
            # Try to find JSON array in response if it's wrapped in text
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)
            
            # Clean up any invalid escape sequences
            response = response.replace('\\', '/')  # Replace backslashes with forward slashes
            
            data = json.loads(response)
            return [
                ExecutionStep(tool=step.get("tool", ""), args=step.get("args", {}))
                for step in data
                if isinstance(step, dict)
            ]
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse plan: {e}")
            logger.debug(f"Response was: {response[:200]}")
            
            # Fallback: try to parse as single tool call
            try:
                # Try parsing as single dict instead of array
                data = json.loads(response)
                if isinstance(data, dict) and "tool" in data:
                    return [ExecutionStep(tool=data["tool"], args=data.get("args", {}))]
            except:
                pass
            
            return []

    async def _format_response(self, results: List[dict], intent: IntentAnalysis) -> str:
        """Format execution results with actual content.

        Args:
            results: Execution results
            intent: Intent analysis

        Returns:
            Formatted response with actual code/content
        """
        if not results:
            return "Completed your request."
        
        parts = []
        parts.extend(format_code_response(results))
        parts.extend(format_test_response(results))
        parts.extend(format_review_response(results))
        parts.extend(format_complexity_response(results))
        
        if not parts:
            return f"Completed {intent.primary_goal} with {len(results)} step(s)."
        return "".join(parts)

    async def _call_model(self, prompt: str) -> str:
        """Call Mistral model with timeout.

        Args:
            prompt: Input prompt

        Returns:
            Model response
        """
        try:
            response = await asyncio.wait_for(
                self.unified_client.make_request(
                    model_name=self.model_name,
                    prompt=prompt,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                ),
                timeout=self.timeout_seconds,
            )
            return response.response if hasattr(response, "response") else str(response)
        except asyncio.TimeoutError:
            logger.error("Model request timed out")
            return "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Model request failed: {e}")
            return f"Error processing request: {str(e)}"

    async def _ensure_conversation(self, conversation_id: str) -> Conversation:
        """Ensure conversation exists.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation entity
        """
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            conversation = Conversation(conversation_id=conversation_id)
            await self.conversation_repo.save(conversation)
        return conversation

