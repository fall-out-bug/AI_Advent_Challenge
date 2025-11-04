"""Model client adapter for multi-pass code review system.

Following Clean Architecture and the Zen of Python.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add shared to path for imports
_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))
shared_path = _root / "shared"
sys.path.insert(0, str(shared_path))

from shared_package.clients.unified_client import UnifiedModelClient

from src.domain.services.token_analyzer import TokenAnalyzer
from src.infrastructure.logging.review_logger import ReviewLogger

logger = logging.getLogger(__name__)


class MultiPassModelAdapter:
    """Adapter for unified model client in multi-pass review context.

    Purpose:
        Provides a simplified interface for calling models in the context
        of multi-pass code review, encapsulating model interaction details
        from pass logic.

    Args:
        unified_client: UnifiedModelClient instance
        model_name: Default model name to use (can be overridden per call)

    Example:
        adapter = MultiPassModelAdapter(
            unified_client, model_name="mistral"
        )
        response = await adapter.send_prompt(
            prompt="Review this code...",
            temperature=0.5,
            max_tokens=1000,
            pass_name="pass_1"
        )
    """

    def __init__(
        self,
        unified_client: UnifiedModelClient,
        model_name: str = "mistral",
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_retry_delay: float = 10.0,
        review_logger: Optional[ReviewLogger] = None,
    ):
        """Initialize adapter.

        Args:
            unified_client: UnifiedModelClient instance
            model_name: Default model name to use
            max_retries: Maximum number of retry attempts
            initial_retry_delay: Initial delay before first retry (seconds)
            backoff_factor: Exponential backoff multiplier
            max_retry_delay: Maximum delay between retries (seconds)
            review_logger: Optional ReviewLogger for detailed logging
        """
        self.client = unified_client
        self.model_name = model_name
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.backoff_factor = backoff_factor
        self.max_retry_delay = max_retry_delay
        self.review_logger = review_logger
        self.logger = logging.getLogger(__name__)

    async def send_prompt(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        pass_name: str = "generic",
        model_name: Optional[str] = None,
    ) -> str:
        """Unified interface for calling model with retry logic.

        Purpose:
            Sends prompt to model with exponential backoff retry.
            Handles logging, error handling, token counting, and truncation.

        Args:
            prompt: Input prompt text
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            pass_name: Name of the pass (for logging/tracking)
            model_name: Optional model name override

        Returns:
            Model response as string

        Raises:
            Exception: If model request fails after all retries

        Example:
            response = await adapter.send_prompt(
                prompt="Review code for quality...",
                temperature=0.5,
                max_tokens=1000,
                pass_name="architecture_pass"
            )
        """
        model_to_use = model_name or self.model_name
        start_time = datetime.now()

        # Structured logging: request start
        self._log_structured(
            pass_name=pass_name,
            event="model_request_start",
            model=model_to_use,
            prompt_length=len(prompt),
            estimated_tokens=self.estimate_tokens(prompt),
            max_tokens=max_tokens,
            temperature=temperature,
        )

        last_error = None
        prompt_to_send = prompt

        for attempt in range(self.max_retries):
            try:
                # Truncate prompt if it exceeds reasonable limits
                if attempt > 0:
                    # On retry, try with truncated prompt (70% of original)
                    truncation_factor = 0.7**attempt
                    if len(prompt_to_send) > 5000:
                        new_length = int(len(prompt) * truncation_factor)
                        prompt_to_send = prompt[:new_length]
                        self.logger.warning(
                            f"[{pass_name}] Retry {attempt + 1}: "
                            f"Truncating prompt to {new_length} chars"
                        )

                # Use UnifiedModelClient.make_request()
                response = await self.client.make_request(
                    model_name=model_to_use,
                    prompt=prompt_to_send,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                execution_time = (datetime.now() - start_time).total_seconds()

                # Structured logging: request success
                self._log_structured(
                    pass_name=pass_name,
                    event="model_request_success",
                    model=model_to_use,
                    response_length=len(response.response),
                    tokens=response.total_tokens,
                    input_tokens=response.input_tokens,
                    output_tokens=response.response_tokens,
                    execution_time_ms=execution_time * 1000,
                    attempt=attempt + 1,
                )

                # Log model interaction via ReviewLogger
                if self.review_logger:
                    self.review_logger.log_model_interaction(
                        prompt=prompt_to_send,
                        response=response.response,
                        pass_name=pass_name,
                        model_name=model_to_use,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        tokens_used={
                            "input_tokens": response.input_tokens,
                            "output_tokens": response.response_tokens,
                            "total_tokens": response.total_tokens,
                        },
                    execution_time_ms=execution_time * 1000,
                    attempt=attempt + 1,
                )

                self.logger.info(
                    f"[{pass_name}] Model response received: "
                    f"{len(response.response)} chars, "
                    f"tokens: {response.total_tokens} (in: {response.input_tokens}, "
                    f"out: {response.response_tokens}), "
                    f"time: {execution_time:.2f}s"
                )

                return response.response

            except Exception as e:
                last_error = e
                execution_time = (datetime.now() - start_time).total_seconds()

                # Structured logging: request error
                self._log_structured(
                    pass_name=pass_name,
                    event="model_request_error",
                    model=model_to_use,
                    error=str(e),
                    error_type=type(e).__name__,
                    execution_time_ms=execution_time * 1000,
                    attempt=attempt + 1,
                    will_retry=attempt < self.max_retries - 1,
                )

                if attempt < self.max_retries - 1:
                    # Calculate exponential backoff delay
                    delay = min(
                        self.initial_retry_delay * (self.backoff_factor**attempt),
                        self.max_retry_delay,
                    )
                    self.logger.warning(
                        f"[{pass_name}] Model error on attempt "
                        f"{attempt + 1}/{self.max_retries}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    # Log retry attempt
                    if self.review_logger:
                        self.review_logger.log_work_step(
                            step=f"model_retry_{attempt + 1}",
                            data={
                                "pass_name": pass_name,
                                "model": model_to_use,
                                "error": str(e),
                                "retry_delay": delay,
                            },
                            status="warning",
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        f"[{pass_name}] Model error after "
                        f"{self.max_retries} attempts: {e}"
                    )

        # All retries exhausted
        raise last_error or Exception("Unknown error in model request")

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Purpose:
            Provides token estimation using TokenAnalyzer.
            Useful for budget management and logging.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count

        Example:
            tokens = adapter.estimate_tokens("Some code to review...")
        """
        return int(TokenAnalyzer.count_tokens(text))

    def truncate_prompt(
        self, prompt: str, max_tokens: int, preserve_end: bool = True
    ) -> str:
        """Truncate prompt to fit within token budget.

        Purpose:
            Intelligently truncates prompt while preserving important parts.
            Default: preserves end (most recent context).

        Args:
            prompt: Original prompt text
            max_tokens: Maximum tokens allowed
            preserve_end: If True, keep the end; if False, keep the beginning

        Returns:
            Truncated prompt string

        Example:
            truncated = adapter.truncate_prompt(long_prompt, max_tokens=3000)
        """
        estimated_tokens = self.estimate_tokens(prompt)

        if estimated_tokens <= max_tokens:
            return prompt

        # Calculate target length (70% of max to leave margin)
        target_tokens = int(max_tokens * 0.7)
        target_length = int(len(prompt) * (target_tokens / estimated_tokens))

        if preserve_end:
            # Keep the end (most recent context)
            return "..." + prompt[-target_length:]
        else:
            # Keep the beginning
            return prompt[:target_length] + "..."

    def _log_structured(self, pass_name: str, event: str, **kwargs) -> None:
        """Log structured JSON event.

        Purpose:
            Logs events in JSON format for easy parsing and analysis.
            Useful for observability and debugging.

        Args:
            pass_name: Name of the pass
            event: Event type (e.g., "model_request_start", "model_request_success")
            **kwargs: Additional event data
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "pass": pass_name,
            "event": event,
            **kwargs,
        }

        # Log as JSON string for structured logging
        self.logger.debug(json.dumps(log_data, default=str))
