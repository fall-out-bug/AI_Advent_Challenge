"""Review logger for structured logging of homework review process.

Following Clean Architecture principles and the Zen of Python.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReviewLogger:
    """Structured logger for homework review process.

    Purpose:
        Provides structured logging in both JSON and text formats
        for all stages of the review process: work steps, review passes,
        model interactions, and reasoning.

    Args:
        session_id: Session ID for this review
        enabled: Whether logging is enabled (default: True)

    Example:
        logger = ReviewLogger(session_id="abc-123")
        logger.log_work_step("extract_archive", {"archive_path": "hw.zip"})
        logger.log_model_interaction(
            prompt="Review this code...",
            response="The code has...",
            tokens=150
        )
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        enabled: bool = True,
    ):
        """Initialize review logger.

        Args:
            session_id: Session ID for this review
            enabled: Whether logging is enabled
        """
        self.session_id = session_id
        self.enabled = enabled
        
        # Storage for logs
        self.work_log_json: List[Dict[str, Any]] = []
        self.review_log_json: List[Dict[str, Any]] = []
        self.model_responses: List[Dict[str, Any]] = []
        self.reasoning_log: List[Dict[str, Any]] = []
        
        # Text logs for readability
        self.work_log_text: List[str] = []
        self.review_log_text: List[str] = []
        
        self.logger = logging.getLogger(__name__)

    def log_work_step(
        self,
        step: str,
        data: Optional[Dict[str, Any]] = None,
        status: str = "info",
    ) -> None:
        """Log a work step event.

        Purpose:
            Logs operational steps like archive extraction, file loading,
            component detection.

        Args:
            step: Step name (e.g., "extract_archive", "load_files", "detect_type")
            data: Optional additional data for this step
            status: Status ("info", "success", "error", "warning")

        Example:
            logger.log_work_step("extract_archive", {
                "archive_path": "hw.zip",
                "extracted_to": "/tmp/xyz"
            })
        """
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "work_step",
            "session_id": self.session_id,
            "step": step,
            "status": status,
            "data": data or {},
        }

        self.work_log_json.append(event)

        # Text format
        text_line = (
            f"[{event['timestamp']}] WORK STEP: {step} "
            f"(status: {status})"
        )
        if data:
            text_line += f" | data: {json.dumps(data, default=str)}"
        self.work_log_text.append(text_line)

        # Standard logger
        log_level = {
            "info": logging.INFO,
            "success": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
        }.get(status, logging.INFO)

        self.logger.log(log_level, f"[{step}] {json.dumps(data, default=str)}")

    def log_review_pass(
        self,
        pass_name: str,
        event: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a review pass event.

        Purpose:
            Logs events during review passes (pass_1, pass_2_docker, etc.)

        Args:
            pass_name: Name of the pass (e.g., "pass_1", "pass_2_docker")
            event: Event type (e.g., "started", "completed", "error")
            data: Optional additional data

        Example:
            logger.log_review_pass("pass_1", "started", {
                "code_length": 5000,
                "detected_components": ["docker"]
            })
        """
        if not self.enabled:
            return

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "review_pass",
            "session_id": self.session_id,
            "pass_name": pass_name,
            "event": event,
            "data": data or {},
        }

        self.review_log_json.append(log_entry)

        # Text format
        text_line = (
            f"[{log_entry['timestamp']}] REVIEW PASS: {pass_name} | "
            f"Event: {event}"
        )
        if data:
            text_line += f" | data: {json.dumps(data, default=str)}"
        self.review_log_text.append(text_line)

        self.logger.info(
            f"[{pass_name}] {event}: {json.dumps(data, default=str)}"
        )

    def log_model_interaction(
        self,
        prompt: str,
        response: str,
        pass_name: str = "generic",
        model_name: str = "mistral",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        tokens_used: Optional[Dict[str, int]] = None,
        execution_time_ms: Optional[float] = None,
        attempt: int = 1,
    ) -> None:
        """Log model interaction (prompt and response).

        Purpose:
            Logs complete model interactions including full prompts,
            responses, token usage, and timing.

        Args:
            prompt: Input prompt sent to model
            response: Model response
            pass_name: Name of the pass making this call
            model_name: Model name used
            temperature: Temperature setting
            max_tokens: Max tokens setting
            tokens_used: Dict with input_tokens, output_tokens, total_tokens
            execution_time_ms: Execution time in milliseconds
            attempt: Retry attempt number

        Example:
            logger.log_model_interaction(
                prompt="Review this code...",
                response="The code has issues...",
                pass_name="pass_1",
                tokens_used={"input_tokens": 100, "output_tokens": 50},
                execution_time_ms=2500.0
            )
        """
        if not self.enabled:
            return

        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "model_interaction",
            "session_id": self.session_id,
            "pass_name": pass_name,
            "model_name": model_name,
            "prompt": prompt,
            "response": response,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "tokens_used": tokens_used or {},
            "execution_time_ms": execution_time_ms,
            "attempt": attempt,
        }

        self.model_responses.append(interaction)

        # Text format - truncated for readability
        prompt_preview = prompt[:200] + "..." if len(prompt) > 200 else prompt
        response_preview = (
            response[:200] + "..." if len(response) > 200 else response
        )
        text_line = (
            f"[{interaction['timestamp']}] MODEL INTERACTION ({pass_name}):\n"
            f"  Model: {model_name} | Temp: {temperature} | "
            f"Max tokens: {max_tokens}\n"
            f"  Prompt: {prompt_preview}\n"
            f"  Response: {response_preview}\n"
        )
        if tokens_used:
            text_line += (
                f"  Tokens: {tokens_used.get('input_tokens', 0)} in, "
                f"{tokens_used.get('output_tokens', 0)} out, "
                f"{tokens_used.get('total_tokens', 0)} total\n"
            )
        if execution_time_ms:
            text_line += f"  Execution time: {execution_time_ms:.2f}ms\n"
        text_line += f"  Attempt: {attempt}\n"
        self.review_log_text.append(text_line)

        self.logger.debug(
            f"[{pass_name}] Model interaction: "
            f"{len(prompt)} chars prompt → {len(response)} chars response"
        )

    def log_reasoning(
        self,
        reasoning: str,
        pass_name: str = "generic",
        context: Optional[str] = None,
    ) -> None:
        """Log model reasoning or analysis.

        Purpose:
            Logs detailed reasoning or analysis steps from the model,
            useful for understanding model decision-making.

        Args:
            reasoning: Reasoning text or analysis
            pass_name: Name of the pass
            context: Optional context for this reasoning

        Example:
            logger.log_reasoning(
                "Analyzing Docker configuration: found 3 services...",
                pass_name="pass_2_docker",
                context="Component analysis"
            )
        """
        if not self.enabled:
            return

        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "reasoning",
            "session_id": self.session_id,
            "pass_name": pass_name,
            "reasoning": reasoning,
            "context": context,
        }

        self.reasoning_log.append(entry)

        # Text format
        text_line = (
            f"[{entry['timestamp']}] REASONING ({pass_name}):\n"
        )
        if context:
            text_line += f"  Context: {context}\n"
        text_line += f"  {reasoning}\n"
        self.review_log_text.append(text_line)

        self.logger.debug(f"[{pass_name}] Reasoning: {reasoning[:100]}...")

    def get_work_log_json(self) -> List[Dict[str, Any]]:
        """Get work log as JSON list."""
        return self.work_log_json.copy()

    def get_work_log_text(self) -> str:
        """Get work log as formatted text."""
        return "\n".join(self.work_log_text)

    def get_review_log_json(self) -> List[Dict[str, Any]]:
        """Get review log as JSON list."""
        return self.review_log_json.copy()

    def get_review_log_text(self) -> str:
        """Get review log as formatted text."""
        return "\n".join(self.review_log_text)

    def get_model_responses(self) -> List[Dict[str, Any]]:
        """Get all model interaction logs."""
        return self.model_responses.copy()

    def get_reasoning_log(self) -> List[Dict[str, Any]]:
        """Get reasoning log."""
        return self.reasoning_log.copy()

    def get_all_logs(self) -> Dict[str, Any]:
        """Get all logs in structured format.

        Returns:
            Dict with all logs organized by type
        """
        return {
            "session_id": self.session_id,
            "work_log_json": self.get_work_log_json(),
            "work_log_text": self.get_work_log_text(),
            "review_log_json": self.get_review_log_json(),
            "review_log_text": self.get_review_log_text(),
            "model_responses": self.get_model_responses(),
            "reasoning_log": self.get_reasoning_log(),
        }

