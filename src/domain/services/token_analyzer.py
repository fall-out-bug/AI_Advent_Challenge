"""Token analyzer domain service.

Following the Zen of Python:
- Simple is better than complex
- Readability counts
- Explicit is better than implicit
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

from src.domain.value_objects.token_info import TokenCount, TokenInfo

# Configure logging
logger = logging.getLogger(__name__)


class TokenAnalyzer:
    """
    Service for analyzing token usage.

    Provides token counting, limit checking, and compression
    recommendations with model-specific configurations.

    Following the Zen of Python:
    - Simple is better than complex
    - Explicit is better than implicit
    """

    # Model-specific token limits
    MODEL_LIMITS = {
        "starcoder": {
            "max_input_tokens": 2048,  # Practical limit
            "max_output_tokens": 1024,
            "recommended_input": 1536,  # 75% of practical
        },
        "mistral": {
            "max_input_tokens": 4096,
            "max_output_tokens": 2048,
            "recommended_input": 3072,
        },
        "qwen": {
            "max_input_tokens": 4096,
            "max_output_tokens": 2048,
            "recommended_input": 3072,
        },
        "tinyllama": {
            "max_input_tokens": 2048,
            "max_output_tokens": 1024,
            "recommended_input": 1536,
        },
    }

    @staticmethod
    def count_tokens(text: str) -> int:
        """
        Count tokens in text using simple approximation.

        Args:
            text: Text to count tokens in

        Returns:
            Estimated token count
        """
        words = text.split()
        return len(words) * 1.3  # Approximate 1.3 tokens per word

    @staticmethod
    def create_token_count(input_text: str, output_text: str) -> TokenCount:
        """
        Create token count from input and output texts.

        Args:
            input_text: Input text
            output_text: Output text

        Returns:
            Token count value object
        """
        input_tokens = int(TokenAnalyzer.count_tokens(input_text))
        output_tokens = int(TokenAnalyzer.count_tokens(output_text))
        total_tokens = input_tokens + output_tokens

        return TokenCount(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

    @staticmethod
    def create_token_info(
        token_count: TokenCount,
        model_name: str,
        metadata: Optional[dict] = None,
    ) -> TokenInfo:
        """
        Create comprehensive token info.

        Args:
            token_count: Token count information
            model_name: Name of the model
            metadata: Optional metadata

        Returns:
            Token info value object
        """
        return TokenInfo(
            token_count=token_count,
            model_name=model_name,
            metadata=metadata,
        )

    @staticmethod
    def analyze_efficiency(token_info: TokenInfo) -> float:
        """
        Analyze token efficiency.

        Args:
            token_info: Token information

        Returns:
            Efficiency score between 0 and 1
        """
        ratio = token_info.token_count.ratio
        if ratio > 2.0:
            return 0.5  # Too verbose
        elif ratio > 1.5:
            return 0.7  # Slightly verbose
        elif ratio > 0.8:
            return 1.0  # Optimal
        else:
            return 0.8  # Too concise

    @classmethod
    def get_model_limits(cls, model_name: str = "starcoder") -> dict:
        """
        Get token limits for a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary with max_input_tokens, max_output_tokens, recommended_input
        """
        return cls.MODEL_LIMITS.get(
            model_name, cls.MODEL_LIMITS["starcoder"]  # Default to starcoder
        ).copy()

    @classmethod
    def check_limit_exceeded(cls, text: str, model_name: str = "starcoder") -> bool:
        """
        Check if text exceeds model token limits.

        Args:
            text: Text to check
            model_name: Name of the model

        Returns:
            True if text exceeds recommended input limits
        """
        limits = cls.get_model_limits(model_name)
        token_count = cls.count_tokens(text)
        return token_count > limits["recommended_input"]

    @classmethod
    def get_recommended_input_tokens(cls, model_name: str = "starcoder") -> int:
        """
        Get recommended input token limit for model.

        Args:
            model_name: Name of the model

        Returns:
            Recommended input token limit
        """
        limits = cls.get_model_limits(model_name)
        return limits["recommended_input"]

    @classmethod
    def count_tokens_batch(cls, texts: List[str]) -> List[int]:
        """
        Count tokens for multiple texts.

        Args:
            texts: List of texts to count tokens for

        Returns:
            List of token counts corresponding to each text
        """
        return [int(cls.count_tokens(text)) for text in texts]

    @classmethod
    def should_compress(cls, text: str, model_name: str = "starcoder") -> bool:
        """
        Determine if text should be compressed.

        Args:
            text: Text to check
            model_name: Name of the model

        Returns:
            True if compression is recommended
        """
        return cls.check_limit_exceeded(text, model_name)

    @classmethod
    def analyze_and_compress(
        cls, text: str, model_name: str = "starcoder", strategy: str = "auto"
    ) -> Tuple[str, dict]:
        """
        Analyze text and compress if needed.

        This method automatically checks if text exceeds model token limits
        and applies compression if necessary.

        Args:
            text: Text to analyze and potentially compress
            model_name: Name of the model
            strategy: Compression strategy ("auto", "truncation", "keywords")

        Returns:
            Tuple of (processed_text, compression_result)
        """
        logger.info(f"Analyzing text for model {model_name}")

        # Count tokens
        token_count = cls.count_tokens(text)
        limits = cls.get_model_limits(model_name)

        # Create result dictionary
        result = {
            "original_tokens": int(token_count),
            "model_name": model_name,
            "max_tokens": limits["recommended_input"],
            "needs_compression": False,
            "compression_applied": False,
            "method": None,
            "compression_ratio": 1.0,
        }

        # Check if compression is needed
        if token_count <= limits["recommended_input"]:
            logger.debug(
                f"Text fits within limits ({token_count} <= {limits['recommended_input']})"
            )
            return text, result

        # Compression needed
        logger.info(
            f"Text exceeds limits ({token_count} > {limits['recommended_input']}), compressing..."
        )
        result["needs_compression"] = True
        result["compression_applied"] = True

        # Apply compression based on strategy
        if strategy == "auto":
            # Use truncation as default for simplicity
            strategy = "truncation"

        compressed_text = cls._apply_compression(
            text, limits["recommended_input"], strategy
        )
        compressed_tokens = cls.count_tokens(compressed_text)

        result["method"] = strategy
        result["compressed_tokens"] = int(compressed_tokens)
        result["compression_ratio"] = (
            compressed_tokens / token_count if token_count > 0 else 1.0
        )

        logger.info(
            f"Compression applied: {result['original_tokens']} -> {result['compressed_tokens']} tokens"
        )

        return compressed_text, result

    @classmethod
    def _apply_compression(cls, text: str, max_tokens: int, strategy: str) -> str:
        """
        Apply compression strategy to text.

        Args:
            text: Text to compress
            max_tokens: Maximum tokens allowed
            strategy: Compression strategy

        Returns:
            Compressed text
        """
        if strategy == "truncation":
            # Simple truncation by words
            words = text.split()
            # Estimate tokens and truncate
            approx_chars = int(max_tokens * 4)  # Rough estimate: 4 chars per token
            char_count = 0
            truncated_words = []

            for word in words:
                if char_count + len(word) + 1 > approx_chars:
                    break
                truncated_words.append(word)
                char_count += len(word) + 1

            return " ".join(truncated_words)

        elif strategy == "keywords":
            # Extract keywords (simple approach: keep important words)
            words = text.split()
            # Keep every other word to reduce tokens while maintaining structure
            return " ".join(words[::2])

        else:
            # Fallback to truncation
            return cls._apply_compression(text, max_tokens, "truncation")
