"""
Token analysis module for counting tokens and checking model limits.

This module provides both simple estimation and accurate token counting
using HuggingFace tokenizers, with configurable limit profiles.

Example:
    Basic usage with simple token counter:
    
    ```python
    from core.token_analyzer import SimpleTokenCounter, LimitProfile
    from models.data_models import TokenInfo
    
    counter = SimpleTokenCounter(LimitProfile.PRACTICAL)
    token_info = counter.count_tokens("Hello world!")
    print(f"Token count: {token_info.count}")
    ```
    
    Advanced usage with accurate token counter:
    
    ```python
    from core.token_analyzer import TokenCounter
    
    counter = TokenCounter("accurate")
    token_info = counter.count_tokens("Hello world!", "starcoder")
    print(f"Accurate count: {token_info.count}")
    ```
"""

from enum import Enum
from typing import Optional

from core.accurate_token_counter import AccurateTokenCounter
from core.interfaces.protocols import ConfigurationProtocol
from models.data_models import ModelLimits, TokenInfo


class LimitProfile(Enum):
    """Limit profile types for model token limits.

    Attributes:
        THEORETICAL: Maximum architecture supports (e.g., 8192 for StarCoder)
        PRACTICAL: Real hardware limits (e.g., 2048 for RTX 3070 Ti 8GB)

    Example:
        ```python
        from core.token_analyzer import LimitProfile

        # Use practical limits for real hardware
        profile = LimitProfile.PRACTICAL
        print(profile.value)  # "practical"
        ```
    """

    THEORETICAL = "theoretical"  # Max architecture supports
    PRACTICAL = "practical"  # Real hardware limits (RTX 3070 Ti 8GB)


class SimpleTokenCounter:
    """
    Simple token counter using word-based estimation.

    Uses 1.3 tokens per word as a rough approximation for token counting.
    This is suitable for demonstration and quick analysis, though not
    as accurate as using actual tokenizers.

    Attributes:
        limit_profile (LimitProfile): Which limit profile to use
        config (Optional[ConfigurationProtocol]): Configuration provider

    Example:
        ```python
        from core.token_analyzer import SimpleTokenCounter, LimitProfile
        from models.data_models import TokenInfo

        # Initialize with practical limits
        counter = SimpleTokenCounter(LimitProfile.PRACTICAL)

        # Count tokens in text
        text = "Hello world! This is a test."
        token_info = counter.count_tokens(text)
        print(f"Estimated tokens: {token_info.count}")

        # Check if text exceeds model limit
        exceeds = counter.check_limit_exceeded(text, "starcoder")
        print(f"Exceeds limit: {exceeds}")
        ```
    """

    def __init__(
        self,
        limit_profile: LimitProfile = LimitProfile.PRACTICAL,
        config: Optional[ConfigurationProtocol] = None,
    ):
        """
        Initialize with limit profile and configuration.

        Args:
            limit_profile: Which limit profile to use (theoretical or practical)
            config: Configuration provider for model limits. If None, uses defaults.

        Example:
            ```python
            from core.token_analyzer import SimpleTokenCounter, LimitProfile

            # Basic initialization
            counter = SimpleTokenCounter()

            # With specific profile
            counter = SimpleTokenCounter(LimitProfile.THEORETICAL)

            # With custom configuration
            counter = SimpleTokenCounter(config=my_config)
            ```
        """
        self.limit_profile = limit_profile
        self.config = config

    def count_tokens(self, text: str, model_name: str = "starcoder") -> TokenInfo:
        """
        Count tokens in text using simple word-based estimation.

        Uses a ratio of 1.3 tokens per word for estimation. This provides
        a quick approximation suitable for demonstration purposes.

        Args:
            text: Input text to count tokens for
            model_name: Name of the model (default: "starcoder")

        Returns:
            TokenInfo: Token count and metadata

        Example:
            ```python
            from core.token_analyzer import SimpleTokenCounter
            from models.data_models import TokenInfo

            counter = SimpleTokenCounter()
            text = "Hello world! This is a test."

            token_info = counter.count_tokens(text, "starcoder")
            print(f"Token count: {token_info.count}")
            print(f"Model: {token_info.model}")
            ```
        """
        if not self._validate_input(text):
            return self._empty_token_info(model_name)

        token_count = self._estimate_tokens(text)
        return self._build_token_info(token_count, model_name)

    def _validate_input(self, text: str) -> bool:
        """Validate input text."""
        return bool(text)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using word-based calculation."""
        word_count = len(text.split())
        return int(word_count * 1.3)

    def _empty_token_info(self, model_name: str) -> TokenInfo:
        """Create empty token info for invalid input."""
        return TokenInfo(count=0, estimated_cost=0.0, model_name=model_name)

    def _build_token_info(self, token_count: int, model_name: str) -> TokenInfo:
        """Build TokenInfo object."""
        return TokenInfo(
            count=token_count,
            estimated_cost=0.0,  # Local models have no cost
            model_name=model_name,
        )

    def get_model_limits(self, model_name: str = "starcoder") -> ModelLimits:
        """
        Get token limits for a specific model.

        Retrieves the token limits for the specified model based on the
        configured limit profile (theoretical or practical).

        Args:
            model_name: Name of the model to get limits for

        Returns:
            ModelLimits: Object containing max_tokens and other limit info

        Raises:
            KeyError: If model name is not found in configuration

        Example:
            ```python
            from core.token_analyzer import SimpleTokenCounter, LimitProfile

            counter = SimpleTokenCounter(LimitProfile.PRACTICAL)
            limits = counter.get_model_limits("starcoder")
            print(f"Max tokens: {limits.max_tokens}")
            print(f"Profile: {limits.profile}")
            ```
        """
        if self.config:
            return self.config.get_model_limits(model_name, self.limit_profile.value)

        # Fallback to default starcoder limits if no config
        return ModelLimits(
            max_input_tokens=4096,
            max_output_tokens=1024,
            max_total_tokens=6000,
            recommended_input=3500,
        )

    def check_limit_exceeded(self, text: str, model_name: str = "starcoder") -> bool:
        """
        Check if text exceeds model's input token limit.

        Compares the estimated token count of the text against the model's
        maximum input token limit for the current profile.

        Args:
            text: Input text to check against limits
            model_name: Name of the model to check limits for

        Returns:
            bool: True if text exceeds the limit, False otherwise

        Example:
            ```python
            from core.token_analyzer import SimpleTokenCounter, LimitProfile

            counter = SimpleTokenCounter(LimitProfile.PRACTICAL)
            long_text = "This is a very long text..." * 100

            exceeds = counter.check_limit_exceeded(long_text, "starcoder")
            if exceeds:
                print("Text exceeds model limit!")
            else:
                print("Text is within limits")
            ```
        """
        token_info = self.count_tokens(text, model_name)
        limits = self.get_model_limits(model_name)
        return self._compare_with_limit(token_info.count, limits.max_input_tokens)

    def _compare_with_limit(self, token_count: int, max_tokens: int) -> bool:
        """Compare token count with limit."""
        return token_count > max_tokens

    def get_available_models(self) -> list[str]:
        """
        Get list of available model names.

        Returns:
            list[str]: List of model names
        """
        if self.config:
            return self.config.get_available_models()

        # Fallback to default models if no config
        return ["starcoder", "mistral", "qwen", "tinyllama"]

    def estimate_compression_target(
        self, text: str, model_name: str = "starcoder", safety_margin: float = 0.9
    ) -> int:
        """
        Estimate target token count for compression.

        Args:
            text: Input text
            model_name: Name of the model
            safety_margin: Safety margin as fraction (0.9 = 90% of limit)

        Returns:
            int: Target token count for compression
        """
        limits = self.get_model_limits(model_name)
        return self._calculate_target_tokens(limits.max_input_tokens, safety_margin)

    def _calculate_target_tokens(self, max_tokens: int, safety_margin: float) -> int:
        """Calculate target tokens with safety margin."""
        return int(max_tokens * safety_margin)

    def set_limit_profile(self, profile: LimitProfile) -> None:
        """
        Set the limit profile to use.

        Args:
            profile: Limit profile to use
        """
        self.limit_profile = profile


class TokenCounter:
    """
    Unified token counter with mode selection.

    Provides a single interface for both simple estimation and
    accurate token counting using HuggingFace tokenizers.

    Attributes:
        mode (str): Counting mode ("simple" or "accurate")
        limit_profile (LimitProfile): Limit profile for model limits
        config (Optional[ConfigurationProtocol]): Configuration provider

    Example:
        ```python
        from core.token_analyzer import TokenCounter, LimitProfile

        # Simple estimation mode
        simple_counter = TokenCounter("simple", LimitProfile.PRACTICAL)
        simple_info = simple_counter.count_tokens("Hello world!")

        # Accurate counting mode
        accurate_counter = TokenCounter("accurate", LimitProfile.THEORETICAL)
        accurate_info = accurate_counter.count_tokens("Hello world!", "starcoder")

        print(f"Simple: {simple_info.count}, Accurate: {accurate_info.count}")
        ```
    """

    def __init__(
        self,
        mode: str = "simple",
        limit_profile: LimitProfile = LimitProfile.PRACTICAL,
        config: Optional[ConfigurationProtocol] = None,
    ):
        """
        Initialize token counter with specified mode.

        Args:
            mode: Counting mode ("simple" for word-based estimation or "accurate" for tokenizer-based)
            limit_profile: Limit profile to use (theoretical or practical)
            config: Configuration provider for model limits. If None, uses defaults.

        Raises:
            ValueError: If mode is not supported

        Example:
            ```python
            from core.token_analyzer import TokenCounter, LimitProfile

            # Initialize simple counter
            counter = TokenCounter("simple", LimitProfile.PRACTICAL)

            # Initialize accurate counter
            accurate_counter = TokenCounter("accurate", LimitProfile.THEORETICAL)

            # With custom configuration
            counter = TokenCounter("simple", config=my_config)
            ```
        """
        if mode == "simple":
            self._counter = SimpleTokenCounter(limit_profile, config)
        elif mode == "accurate":
            self._counter = AccurateTokenCounter()
            # Store limit profile separately for accurate mode
            self._limit_profile = limit_profile
            self._config = config
        else:
            raise ValueError(f"Unknown mode: {mode}")

        self.mode = mode

    def count_tokens(self, text: str, model_name: str = "starcoder") -> TokenInfo:
        """
        Count tokens using the configured mode.

        Args:
            text: Input text to count tokens for
            model_name: Name of the model

        Returns:
            TokenInfo: Token count and metadata
        """
        return self._counter.count_tokens(text, model_name)

    def get_model_limits(self, model_name: str = "starcoder") -> ModelLimits:
        """
        Get token limits for a specific model.

        Retrieves the token limits for the specified model based on the
        configured limit profile (theoretical or practical).

        Args:
            model_name: Name of the model to get limits for

        Returns:
            ModelLimits: Object containing max_tokens and other limit info

        Example:
            ```python
            from core.token_analyzer import SimpleTokenCounter, LimitProfile

            counter = SimpleTokenCounter(LimitProfile.PRACTICAL)
            limits = counter.get_model_limits("starcoder")
            print(f"Max tokens: {limits.max_tokens}")
            print(f"Profile: {limits.profile}")
            ```
        """
        if self.mode == "accurate":
            return self._get_limits_for_accurate_mode(model_name)
        else:
            return self._counter.get_model_limits(model_name)

    def _get_limits_for_accurate_mode(self, model_name: str) -> ModelLimits:
        """Get limits for accurate mode using SimpleTokenCounter."""
        simple_counter = SimpleTokenCounter(self._limit_profile, self._config)
        return simple_counter.get_model_limits(model_name)

    def check_limit_exceeded(self, text: str, model_name: str = "starcoder") -> bool:
        """
        Check if text exceeds model's input token limit.

        Args:
            text: Input text to check
            model_name: Name of the model

        Returns:
            bool: True if limit is exceeded, False otherwise
        """
        token_info = self.count_tokens(text, model_name)
        limits = self.get_model_limits(model_name)
        return self._compare_with_limit(token_info.count, limits.max_input_tokens)

    def _compare_with_limit(self, token_count: int, max_tokens: int) -> bool:
        """Compare token count with limit."""
        return token_count > max_tokens

    def get_available_models(self) -> list[str]:
        """
        Get list of available model names.

        Returns:
            list[str]: List of model names
        """
        return self._counter.get_available_models()

    def estimate_compression_target(
        self, text: str, model_name: str = "starcoder", safety_margin: float = 0.9
    ) -> int:
        """
        Estimate target token count for compression.

        Args:
            text: Input text
            model_name: Name of the model
            safety_margin: Safety margin as fraction

        Returns:
            int: Target token count for compression
        """
        limits = self.get_model_limits(model_name)
        return self._calculate_target_tokens(limits.max_input_tokens, safety_margin)

    def _calculate_target_tokens(self, max_tokens: int, safety_margin: float) -> int:
        """Calculate target tokens with safety margin."""
        return int(max_tokens * safety_margin)

    def set_limit_profile(self, profile: LimitProfile) -> None:
        """
        Set the limit profile to use.

        Args:
            profile: Limit profile to use
        """
        if self.mode == "simple":
            self._counter.set_limit_profile(profile)
        else:
            self._limit_profile = profile
