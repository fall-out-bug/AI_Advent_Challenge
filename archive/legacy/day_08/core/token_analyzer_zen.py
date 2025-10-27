"""
Zen Python Token Analyzer - Refactored following Python Zen principles.

Key improvements:
1. Flat is better than nested - simplified MODEL_LIMITS structure
2. Explicit is better than implicit - clear constants and type hints
3. Simple is better than complex - cleaner class design
4. Readability counts - better naming and documentation
5. Errors should never pass silently - proper error handling
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from core.accurate_token_counter import AccurateTokenCounter
from models.data_models import ModelLimits, TokenInfo


class LimitProfile(Enum):
    """Limit profile types - explicit and clear."""

    THEORETICAL = "theoretical"  # Max architecture supports
    PRACTICAL = "practical"  # Real hardware limits (RTX 3070 Ti 8GB)


# Constants following "Explicit is better than implicit"
# Flat structure following "Flat is better than nested"

# StarCoder limits
STARCODER_THEORETICAL = ModelLimits(
    max_input_tokens=16384,  # Full context window
    max_output_tokens=2048,
    max_total_tokens=16384,
    sliding_window=4096,  # Attention window
)

STARCODER_PRACTICAL = ModelLimits(
    max_input_tokens=4096,  # Safe for 8GB GPU
    max_output_tokens=1024,
    max_total_tokens=6000,  # With flash-attn buffer
    recommended_input=3500,  # Conservative target
)

# Mistral limits
MISTRAL_THEORETICAL = ModelLimits(
    max_input_tokens=32768, max_output_tokens=2048, max_total_tokens=32768
)

MISTRAL_PRACTICAL = ModelLimits(
    max_input_tokens=8192,  # Conservative for 8GB GPU
    max_output_tokens=1024,
    max_total_tokens=10000,
)

# Qwen limits
QWEN_THEORETICAL = ModelLimits(
    max_input_tokens=32768, max_output_tokens=2048, max_total_tokens=32768
)

QWEN_PRACTICAL = ModelLimits(
    max_input_tokens=8192,  # Conservative for 8GB GPU
    max_output_tokens=1024,
    max_total_tokens=10000,
)

# TinyLlama limits
TINYLLAMA_LIMITS = ModelLimits(
    max_input_tokens=2048, max_output_tokens=512, max_total_tokens=2048
)

# Model limits mapping - simple and explicit
MODEL_LIMITS_MAP: Dict[str, Dict[LimitProfile, ModelLimits]] = {
    "starcoder": {
        LimitProfile.THEORETICAL: STARCODER_THEORETICAL,
        LimitProfile.PRACTICAL: STARCODER_PRACTICAL,
    },
    "mistral": {
        LimitProfile.THEORETICAL: MISTRAL_THEORETICAL,
        LimitProfile.PRACTICAL: MISTRAL_PRACTICAL,
    },
    "qwen": {
        LimitProfile.THEORETICAL: QWEN_THEORETICAL,
        LimitProfile.PRACTICAL: QWEN_PRACTICAL,
    },
    "tinyllama": {
        LimitProfile.THEORETICAL: TINYLLAMA_LIMITS,
        LimitProfile.PRACTICAL: TINYLLAMA_LIMITS,
    },
}

# Constants for token estimation
TOKENS_PER_WORD_ESTIMATE = 1.3
DEFAULT_MODEL = "starcoder"


class TokenCounterError(Exception):
    """Custom exception for token counter errors."""

    pass


class SimpleTokenCounter:
    """
    Simple token counter using word-based estimation.

    Following Zen principles:
    - Simple is better than complex
    - Explicit is better than implicit
    - Errors should never pass silently
    """

    def __init__(self, limit_profile: LimitProfile = LimitProfile.PRACTICAL):
        """
        Initialize token counter with specified limit profile.

        Args:
            limit_profile: Which limit profile to use (theoretical/practical)
        """
        self.limit_profile = limit_profile

    def count_tokens(self, text: str, model_name: str = DEFAULT_MODEL) -> TokenInfo:
        """
        Count tokens in text using simple word-based estimation.

        Args:
            text: Input text to count tokens for
            model_name: Name of the model

        Returns:
            TokenInfo with token count and metadata

        Raises:
            TokenCounterError: If text is invalid
        """
        if not isinstance(text, str):
            raise TokenCounterError(f"Text must be string, got {type(text)}")

        if not text.strip():
            return TokenInfo(count=0, estimated_cost=0.0, model_name=model_name)

        # Simple estimation: words * tokens_per_word
        word_count = len(text.split())
        token_count = int(word_count * TOKENS_PER_WORD_ESTIMATE)

        return TokenInfo(
            count=token_count,
            estimated_cost=0.0,  # No cost estimation in simple mode
            model_name=model_name,
        )

    def get_model_limits(self, model_name: str = DEFAULT_MODEL) -> ModelLimits:
        """
        Get token limits for specified model and profile.

        Args:
            model_name: Name of the model

        Returns:
            ModelLimits for the model

        Raises:
            TokenCounterError: If model not supported
        """
        if model_name not in MODEL_LIMITS_MAP:
            # Default to starcoder if unknown model
            model_name = DEFAULT_MODEL

        try:
            return MODEL_LIMITS_MAP[model_name][self.limit_profile]
        except KeyError as e:
            raise TokenCounterError(
                f"Limit profile {self.limit_profile} not found for {model_name}"
            ) from e

    def check_limit_exceeded(self, text: str, model_name: str = DEFAULT_MODEL) -> bool:
        """
        Check if text exceeds model's input token limit.

        Args:
            text: Input text to check
            model_name: Name of the model

        Returns:
            True if limit exceeded, False otherwise
        """
        token_info = self.count_tokens(text, model_name)
        limits = self.get_model_limits(model_name)
        return token_info.count > limits.max_input_tokens

    def estimate_compression_target(
        self, text: str, model_name: str = DEFAULT_MODEL, safety_margin: float = 0.9
    ) -> int:
        """
        Estimate target token count for compression.

        Args:
            text: Input text
            model_name: Name of the model
            safety_margin: Safety margin (0.0-1.0)

        Returns:
            Target token count for compression
        """
        if not 0.0 <= safety_margin <= 1.0:
            raise TokenCounterError(
                f"Safety margin must be 0.0-1.0, got {safety_margin}"
            )

        limits = self.get_model_limits(model_name)
        return int(limits.max_input_tokens * safety_margin)

    def get_available_models(self) -> list[str]:
        """
        Get list of available models.

        Returns:
            List of model names
        """
        return list(MODEL_LIMITS_MAP.keys())

    def set_limit_profile(self, profile: LimitProfile) -> None:
        """
        Change the limit profile.

        Args:
            profile: New limit profile
        """
        self.limit_profile = profile


class TokenCounter:
    """
    Unified token counter with mode selection.

    Following Zen principles:
    - There should be one obvious way to do it
    - Simple is better than complex
    """

    def __init__(
        self, mode: str = "simple", limit_profile: LimitProfile = LimitProfile.PRACTICAL
    ):
        """
        Initialize unified token counter.

        Args:
            mode: Counting mode ("simple" or "accurate")
            limit_profile: Limit profile to use
        """
        if mode == "simple":
            self._counter = SimpleTokenCounter(limit_profile)
        elif mode == "accurate":
            self._counter = AccurateTokenCounter()
            self._limit_profile = limit_profile
        else:
            raise TokenCounterError(f"Unknown mode: {mode}. Use 'simple' or 'accurate'")

        self.mode = mode

    def count_tokens(self, text: str, model_name: str = DEFAULT_MODEL) -> TokenInfo:
        """Count tokens using selected mode."""
        return self._counter.count_tokens(text, model_name)

    def get_model_limits(self, model_name: str = DEFAULT_MODEL) -> ModelLimits:
        """Get model limits (always uses SimpleTokenCounter for consistency)."""
        if self.mode == "accurate":
            # Use SimpleTokenCounter for limits even in accurate mode
            simple_counter = SimpleTokenCounter(self._limit_profile)
            return simple_counter.get_model_limits(model_name)
        return self._counter.get_model_limits(model_name)

    def check_limit_exceeded(self, text: str, model_name: str = DEFAULT_MODEL) -> bool:
        """Check if text exceeds limits."""
        return self._counter.check_limit_exceeded(text, model_name)

    def estimate_compression_target(
        self, text: str, model_name: str = DEFAULT_MODEL, safety_margin: float = 0.9
    ) -> int:
        """Estimate compression target."""
        return self._counter.estimate_compression_target(
            text, model_name, safety_margin
        )

    def get_available_models(self) -> list[str]:
        """Get available models."""
        return self._counter.get_available_models()

    def set_limit_profile(self, profile: LimitProfile) -> None:
        """Set limit profile."""
        if self.mode == "accurate":
            self._limit_profile = profile
        else:
            self._counter.set_limit_profile(profile)
