"""God Agent Telegram handler.

Purpose:
    Handles all Telegram messages (text and voice) through GodAgentOrchestrator,
    extending existing Butler bot without breaking changes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from typing import Any
else:
    Any = object

from aiogram import F, Router
from aiogram.types import Message

from src.application.god_agent.services.god_agent_orchestrator import (
    GodAgentOrchestrator,
)
from src.application.god_agent.services.intent_router_service import (
    IntentRouterService,
)
from src.application.god_agent.services.plan_compiler_service import (
    PlanCompilerService,
)
from src.infrastructure.god_agent.adapters.voice_pipeline_adapter import (
    VoicePipelineAdapter,
)
from src.infrastructure.logging import get_logger

logger = get_logger("god_agent_handler")

# Global instances (set by setup_god_agent_handler)
_orchestrator: Optional[GodAgentOrchestrator] = None
_intent_router: Optional[IntentRouterService] = None
_plan_compiler: Optional[PlanCompilerService] = None
_voice_adapter: Optional[VoicePipelineAdapter] = None


def setup_god_agent_handler(
    orchestrator: GodAgentOrchestrator,
    intent_router: IntentRouterService,
    plan_compiler: PlanCompilerService,
    voice_adapter: Optional[VoicePipelineAdapter] = None,
) -> Router:
    """Setup God Agent handler with dependencies.

    Purpose:
        Configure router with orchestrator, intent router, plan compiler,
        and optional voice adapter dependencies for handler functions.

    Args:
        orchestrator: GodAgentOrchestrator instance for plan execution.
        intent_router: IntentRouterService for intent classification.
        plan_compiler: PlanCompilerService for plan generation.
        voice_adapter: Optional VoicePipelineAdapter for voice transcription.

    Returns:
        Configured aiogram Router.

    Example:
        >>> router = setup_god_agent_handler(
        ...     orchestrator=orchestrator,
        ...     intent_router=intent_router,
        ...     plan_compiler=plan_compiler,
        ...     voice_adapter=voice_adapter
        ... )
        >>> dp.include_router(router)
    """
    global _orchestrator, _intent_router, _plan_compiler, _voice_adapter
    _orchestrator = orchestrator
    _intent_router = intent_router
    _plan_compiler = plan_compiler
    _voice_adapter = voice_adapter

    router = Router()
    # Register text message handler
    router.message.register(handle_text_message, F.text)
    # Register voice/audio message handler
    router.message.register(
        handle_voice_message,
        F.content_type.in_(["voice", "audio"]),
    )
    return router


async def handle_text_message(message: Message) -> None:
    """Handle text message through God Agent orchestrator.

    Purpose:
        Process text message: classify intent, generate plan, execute plan,
        and send response to user.

    Args:
        message: Telegram message object.

    Example:
        >>> await handle_text_message(message)
    """
    if not _orchestrator or not _intent_router or not _plan_compiler:
        logger.error("God Agent handler not initialized")
        await message.answer("Service temporarily unavailable")
        return

    try:
        if not message.from_user:
            await message.answer("User information not available")
            return

        user_id = str(message.from_user.id)
        user_message = message.text or ""

        logger.info(
            "Processing text message",
            extra={"user_id": user_id, "message_length": len(user_message)},
        )

        # Step 1: Classify intent
        # Simplified: get memory snapshot (would be injected in real implementation)
        # For now, create a minimal snapshot
        from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
        memory_snapshot = MemorySnapshot(
            user_id=user_id,
            profile_summary="",
            conversation_summary="",
            rag_hits=[],
            artifact_refs=[],
        )

        intent = await _intent_router.route_intent(user_id, user_message)

        # Step 2: Generate plan
        task_plan = await _plan_compiler.compile_plan(
            intent=intent,
            memory_snapshot=memory_snapshot,
        )

        # Step 3: Execute plan
        result = await _orchestrator.execute_plan(
            task_plan=task_plan,
            user_id=user_id,
        )

        # Step 4: Format and send response
        response_text = _format_response(result)
        await message.answer(response_text)

        logger.info(
            "Text message processed",
            extra={"user_id": user_id, "plan_id": result.get("plan_id")},
        )

    except Exception as e:
        user_id_str = str(message.from_user.id) if message.from_user else "unknown"
        logger.error(
            "Failed to process text message",
            extra={"user_id": user_id_str, "error": str(e)},
            exc_info=True,
        )
        await message.answer("Sorry, I encountered an error. Please try again.")


async def handle_voice_message(message: Message) -> None:
    """Handle voice message through God Agent orchestrator.

    Purpose:
        Transcribe voice message, then process through orchestrator
        (same flow as text message).

    Args:
        message: Telegram message object with voice/audio.

    Example:
        >>> await handle_voice_message(message)
    """
    if not _orchestrator or not _intent_router or not _plan_compiler:
        logger.error("God Agent handler not initialized")
        await message.answer("Service temporarily unavailable")
        return

    try:
        if not message.from_user:
            await message.answer("User information not available")
            return

        user_id = str(message.from_user.id)

        logger.info(
            "Processing voice message",
            extra={"user_id": user_id},
        )

        # Step 1: Transcribe voice
        if _voice_adapter:
            transcribed_text = await _voice_adapter.transcribe_voice(message)
        else:
            transcribed_text = await _transcribe_voice(message)

        if not transcribed_text:
            await message.answer("Sorry, I couldn't understand the voice message.")
            return

        # Step 2: Process as text message
        # Create a text message object for processing
        message.text = transcribed_text
        await handle_text_message(message)

        logger.info(
            "Voice message processed",
            extra={"user_id": user_id, "transcribed_length": len(transcribed_text)},
        )

    except Exception as e:
        user_id_str = str(message.from_user.id) if message.from_user else "unknown"
        logger.error(
            "Failed to process voice message",
            extra={"user_id": user_id_str, "error": str(e)},
            exc_info=True,
        )
        await message.answer("Sorry, I encountered an error processing the voice message.")


async def _transcribe_voice(message: Message) -> str:
    """Transcribe voice message to text.

    Purpose:
        Download voice file and transcribe using STT service.

    Args:
        message: Telegram message with voice/audio.

    Returns:
        Transcribed text or empty string if transcription fails.

    Example:
        >>> text = await _transcribe_voice(message)
        >>> text
        'Hello, how can you help me?'
    """
    # Simplified: would use ProcessVoiceCommandUseCase or STT service
    # For now, return placeholder
    logger.warning("Voice transcription not fully implemented")
    return ""


def _format_response(result: dict[str, Any]) -> str:
    """Format orchestrator result as response text.

    Purpose:
        Convert execution result to user-friendly text response.

    Args:
        result: Execution result dictionary.

    Returns:
        Formatted response text.

    Example:
        >>> response = _format_response({"status": "completed", "step_results": [...]})
        >>> response
        'Task completed successfully.'
    """
    status: str = result.get("status", "unknown")
    step_results: list[dict[str, Any]] = result.get("step_results", [])

    if status == "completed":
        if step_results:
            # Extract output from first successful step
            for step_result in step_results:
                if step_result.get("status") == "success":
                    output: dict[str, Any] = step_result.get("output", {})
                    if "reply" in output:
                        reply: str = str(output["reply"])
                        return reply
                    if "answer" in output:
                        answer: str = str(output["answer"])
                        return answer
        return "Task completed successfully."
    elif status == "failed":
        return "Sorry, the task failed. Please try again."
    else:
        return "Task is in progress..."


class GodAgentTelegramHandler:
    """God Agent Telegram handler class.

    Purpose:
        Encapsulates handler logic for dependency injection and testing.

    Attributes:
        orchestrator: GodAgentOrchestrator instance.
        intent_router: IntentRouterService instance.
        plan_compiler: PlanCompilerService instance.
    """

    def __init__(
        self,
        orchestrator: GodAgentOrchestrator,
        intent_router: IntentRouterService,
        plan_compiler: PlanCompilerService,
        voice_adapter: Optional[VoicePipelineAdapter] = None,
    ) -> None:
        """Initialize handler.

        Args:
            orchestrator: GodAgentOrchestrator instance.
            intent_router: IntentRouterService instance.
            plan_compiler: PlanCompilerService instance.
            voice_adapter: Optional VoicePipelineAdapter instance.
        """
        self.orchestrator = orchestrator
        self.intent_router = intent_router
        self.plan_compiler = plan_compiler
        self.voice_adapter = voice_adapter

    async def handle_text_message(self, message: Message) -> None:
        """Handle text message.

        Args:
            message: Telegram message object.
        """
        await handle_text_message(message)

    async def handle_voice_message(self, message: Message) -> None:
        """Handle voice message.

        Args:
            message: Telegram message object.
        """
        await handle_voice_message(message)
