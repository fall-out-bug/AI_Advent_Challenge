"""Base class for all review passes.

Following Clean Architecture principles and the Zen of Python.
"""

import json
import logging
import re
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

# Add shared to path for imports
_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(_root))
shared_path = _root / "shared"
sys.path.insert(0, str(shared_path))

from shared_package.clients.unified_client import UnifiedModelClient

from src.domain.agents.session_manager import SessionManager
from src.domain.models.code_review_models import PassFindings
from src.infrastructure.adapters.multi_pass_model_adapter import MultiPassModelAdapter
from src.infrastructure.logging.review_logger import ReviewLogger
from src.infrastructure.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class BaseReviewPass(ABC):
    """Abstract base class for all review passes.

    Purpose:
        Provides common functionality for all review passes:
        - Model interaction through adapter
        - Prompt loading
        - Token estimation
        - Logging and error handling

    Args:
        unified_client: UnifiedModelClient instance
        session_manager: SessionManager for state persistence
        token_budget: Token budget for this pass
        model_name: Optional model name override

    Example:
        class MyPass(BaseReviewPass):
            async def run(self, code: str) -> PassFindings:
                prompt = self._load_prompt_template("my_prompt")
                response = await self._call_mistral(prompt)
                return self._parse_response(response)
    """

    def __init__(
        self,
        unified_client: UnifiedModelClient,
        session_manager: SessionManager,
        token_budget: int = 2000,
        model_name: Optional[str] = None,
        review_logger: Optional[ReviewLogger] = None,
    ):
        """Initialize base review pass.

        Args:
            unified_client: UnifiedModelClient instance
            session_manager: SessionManager for state persistence
            token_budget: Token budget for this pass
            model_name: Optional model name override
            review_logger: Optional ReviewLogger for detailed logging
        """
        self.review_logger = review_logger
        self.adapter = MultiPassModelAdapter(
            unified_client,
            model_name=model_name or "mistral",
            review_logger=review_logger,
        )
        self.session = session_manager
        self.token_budget = token_budget
        self.used_tokens: int = 0
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _call_mistral(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Call model through adapter with token budget management.

        Purpose:
            Unified interface for calling the model with token budget tracking.
            Handles logging, error handling, and automatic truncation.

        Args:
            prompt: Input prompt text
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Model response as string

        Raises:
            Exception: If model call fails

        Example:
            response = await self._call_mistral(
                prompt="Review this code...",
                temperature=0.5,
                max_tokens=1000
            )
        """
        pass_name = self.__class__.__name__

        # Estimate tokens and check budget
        estimated_tokens = self.adapter.estimate_tokens(prompt)
        remaining_budget = self.token_budget - self.used_tokens

        # Check if prompt exceeds remaining budget
        if estimated_tokens > remaining_budget:
            self.logger.warning(
                f"[{pass_name}] Prompt estimated tokens ({estimated_tokens}) "
                f"exceed remaining budget ({remaining_budget}). Truncating..."
            )

            # Truncate prompt to fit within budget (preserve end - most recent context)
            truncated_prompt = self.adapter.truncate_prompt(
                prompt=prompt,
                max_tokens=int(remaining_budget * 0.9),  # Use 90% of remaining budget
                preserve_end=True,
            )

            new_estimated = self.adapter.estimate_tokens(truncated_prompt)
            self.logger.info(
                f"[{pass_name}] Truncated prompt: "
                f"{len(prompt)} → {len(truncated_prompt)} chars, "
                f"{estimated_tokens} → {new_estimated} tokens"
            )
            prompt = truncated_prompt

        # Adjust max_tokens if it would exceed remaining budget
        if max_tokens > remaining_budget:
            old_max = max_tokens
            max_tokens = max(
                int(remaining_budget * 0.8), 100
            )  # Leave 20% margin, min 100
            self.logger.warning(
                f"[{pass_name}] Adjusted max_tokens: {old_max} → {max_tokens} "
                f"(remaining budget: {remaining_budget})"
            )

        # Call adapter
        response = await self.adapter.send_prompt(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            pass_name=pass_name,
        )

        # Track used tokens (rough estimate)
        response_tokens = self.adapter.estimate_tokens(response)
        self.used_tokens += estimated_tokens + response_tokens

        self.logger.debug(
            f"[{pass_name}] Token usage: "
            f"{estimated_tokens} input + {response_tokens} output = "
            f"{estimated_tokens + response_tokens} total. "
            f"Budget: {self.used_tokens}/{self.token_budget}"
        )

        return response

    def _load_prompt_template(self, template_name: str) -> str:
        """Load prompt template from prompts/v1/.

        Purpose:
            Loads prompt template using PromptLoader.

        Args:
            template_name: Name of prompt from registry

        Returns:
            Prompt template content

        Raises:
            ValueError: If prompt not found
            FileNotFoundError: If prompt file missing

        Example:
            template = self._load_prompt_template("pass_1_architecture")
        """
        return PromptLoader.load_prompt(template_name)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Purpose:
            Provides token estimation for budget management.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count

        Example:
            tokens = self._estimate_tokens("Some text...")
        """
        return self.adapter.estimate_tokens(text)

    def get_remaining_budget(self) -> int:
        """Get remaining token budget for this pass.

        Purpose:
            Returns how many tokens are still available.

        Returns:
            Remaining token budget

        Example:
            remaining = self.get_remaining_budget()
            if remaining < 500:
                logger.warning("Low token budget remaining")
        """
        return max(0, self.token_budget - self.used_tokens)

    def can_afford(self, estimated_tokens: int) -> bool:
        """Check if estimated tokens fit within remaining budget.

        Purpose:
            Helper method to check if operation fits in budget.

        Args:
            estimated_tokens: Estimated tokens needed

        Returns:
            True if operation fits, False otherwise

        Example:
            if not self.can_afford(estimated_tokens):
                # Adjust operation
        """
        return estimated_tokens <= self.get_remaining_budget()

    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from model response.

        Purpose:
            Intelligently extracts JSON from model response by:
            1. Checking all ```json code blocks for valid JSON (taking last valid one)
            2. If no valid JSON in blocks, searching for standalone JSON objects in text
            3. Returns None if no valid JSON found (caller should use fallback)

        Args:
            response: Raw response text from model

        Returns:
            Parsed JSON dictionary or None if not found/invalid

        Example:
            json_data = self._extract_json_from_response(response)
            if json_data:
                return json_data
            else:
                # Use fallback text parsing
        """
        # Step 1: Try to extract JSON from ```json code blocks
        json_matches = list(re.finditer(r"```json\s*(.*?)\s*```", response, re.DOTALL))
        if json_matches:
            # Check all matches from last to first, return first valid JSON
            for match in reversed(json_matches):
                json_text = match.group(1).strip()
                try:
                    parsed = json.loads(json_text)
                    self.logger.debug(f"Found valid JSON in ```json block (length: {len(json_text)})")
                    return parsed
                except json.JSONDecodeError:
                    continue

        # Step 2: Try to find standalone JSON objects in text
        # Look for patterns like { ... } with proper nesting
        # Start from the end (model usually puts final answer at the end)
        text_to_search = response.strip()
        
        # Find all potential JSON start positions (opening braces)
        brace_positions = []
        for i, char in enumerate(text_to_search):
            if char == '{':
                brace_positions.append(i)
        
        # Try to parse JSON starting from each brace position (backwards)
        for start_pos in reversed(brace_positions):
            # Try to find matching closing brace
            brace_count = 0
            end_pos = None
            in_string = False
            escape_next = False
            
            for i in range(start_pos, len(text_to_search)):
                char = text_to_search[i]
                
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i + 1
                            break
            
            if end_pos:
                json_candidate = text_to_search[start_pos:end_pos]
                # Only try to parse if it looks like substantial JSON (at least 50 chars)
                if len(json_candidate) >= 50:
                    try:
                        parsed = json.loads(json_candidate)
                        self.logger.debug(f"Found valid standalone JSON (length: {len(json_candidate)})")
                        return parsed
                    except json.JSONDecodeError:
                        continue

        # Step 3: Try direct JSON parse of entire response (unlikely but worth trying)
        try:
            parsed = json.loads(response.strip())
            self.logger.debug("Entire response is valid JSON")
            return parsed
        except json.JSONDecodeError:
            pass

        # No valid JSON found
        self.logger.debug("No valid JSON found in response")
        return None

    @abstractmethod
    async def run(self, *args, **kwargs) -> PassFindings:
        """Execute the pass and return findings.

        Purpose:
            Abstract method that must be implemented by subclasses.
            Performs the actual review pass logic.

        Returns:
            PassFindings with results from this pass

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement run() method")
