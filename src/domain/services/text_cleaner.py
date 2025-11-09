"""Text cleaning service for summarization."""

from __future__ import annotations

import json
import re


class TextCleanerService:
    """Service for cleaning text for summarization and LLM responses.

    Purpose:
        Provides methods to clean text before summarization
        and clean LLM responses from artifacts (JSON, Markdown, etc.).
    """

    @staticmethod
    def clean_for_summarization(text: str, max_length_per_item: int = 500) -> str:
        """Clean text before summarization.

        Purpose:
            Removes URLs, UTM parameters, extra whitespace,
            and truncates to reasonable length.

        Args:
            text: Raw text to clean.
            max_length_per_item: Maximum characters per text item (default: 500).

        Returns:
            Cleaned text.
        """
        # Remove URLs
        text = re.sub(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "",
            text,
        )
        # Remove UTM parameters references
        text = re.sub(r"utm_[a-z_]+", "", text, flags=re.IGNORECASE)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove trailing "читать далее" etc. and trailing ellipsis
        text = re.sub(
            r"\s*(читать\s+далее|read\s+more|подробнее|\.\.\.)\s*$",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"[\.…]+\s*$", "", text)

        # Truncate if too long
        if len(text) > max_length_per_item:
            text = text[:max_length_per_item]

        return text.strip()

    @staticmethod
    def clean_llm_response(response: str) -> str:
        """Clean LLM response from JSON and Markdown artifacts.

        Purpose:
            Removes JSON structures, Markdown formatting,
            numbering, and other artifacts from LLM responses.

        Args:
            response: Raw LLM response text.

        Returns:
            Cleaned plain text.
        """
        if not response:
            return ""

        cleaned = response.strip()

        # Try to extract text from JSON if response starts with JSON
        if cleaned.startswith("{") or cleaned.startswith("["):
            cleaned = TextCleanerService._extract_text_from_json(cleaned)

        # Remove JSON objects and arrays using regex
        cleaned = re.sub(r"\{[^{}]*\}", "", cleaned)  # Remove JSON objects
        cleaned = re.sub(r"\[[^\[\]]*\]", "", cleaned)  # Remove JSON arrays

        # Remove JSON-like field patterns: "key": "value"
        cleaned = re.sub(r'["\']?\w+["\']?\s*:\s*["\']?([^"\']+)["\']?', r"\1", cleaned)

        # Remove common JSON artifacts
        cleaned = (
            cleaned.replace("{", "").replace("}", "").replace("[", "").replace("]", "")
        )
        cleaned = re.sub(r'["\']', "", cleaned)  # Remove quotes

        # Remove numbering patterns (1., 2., First post, Second post, etc.)
        cleaned = re.sub(r"^\d+\.\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(
            r"^(In the )?(first|second|third|fourth|fifth|First|Second|Third)\s+post",
            "",
            cleaned,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        cleaned = re.sub(
            r"^The (first|second|third|fourth|fifth)\s+post",
            "",
            cleaned,
            flags=re.IGNORECASE | re.MULTILINE,
        )

        # Remove Markdown artifacts
        cleaned = re.sub(r"[*_`\[\]()]", "", cleaned)
        # Remove bullet points
        cleaned = re.sub(r"^[•\-\*]\s*", "", cleaned, flags=re.MULTILINE)

        # Normalize quotes (smart quotes to regular)
        cleaned = (
            cleaned.replace('"', '"')
            .replace('"', '"')
            .replace(""", "'").replace(""", "'")
        )

        # Normalize whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned

    @staticmethod
    def _extract_text_from_json(text: str) -> str:
        """Extract text content from JSON structure.

        Args:
            text: Text that may contain JSON.

        Returns:
            Extracted text or original if extraction fails.
        """
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                # Look for 'summary', 'text', 'content', or 'response' fields
                for key in ["summary", "text", "content", "response", "message"]:
                    if key in parsed and isinstance(parsed[key], str):
                        return parsed[key]
                # If no text field found, try to concatenate string values
                text_parts = [str(v) for v in parsed.values() if isinstance(v, str)]
                if text_parts:
                    return " ".join(text_parts)
            elif isinstance(parsed, list):
                # If it's a list, try to join string elements
                text_parts = [str(item) for item in parsed if isinstance(item, str)]
                if text_parts:
                    return " ".join(text_parts)
        except (json.JSONDecodeError, ValueError):
            pass

        # If JSON parsing fails, return original
        return text

    @staticmethod
    def deduplicate_sentences(
        sentences: list[str], threshold: float = 0.6
    ) -> list[str]:
        """Remove duplicate or very similar sentences.

        Purpose:
            Filters out sentences with high word overlap (>threshold).

        Args:
            sentences: List of sentence strings.
            threshold: Similarity threshold (0.0-1.0). Sentences with
                word overlap > threshold are considered duplicates.

        Returns:
            List of unique sentences.
        """
        unique_sentences: list[str] = []

        for sent in sentences:
            is_duplicate = False
            sent_words = set(sent.lower().split())

            for existing in unique_sentences:
                existing_words = set(existing.lower().split())
                overlap = (
                    len(sent_words & existing_words)
                    / max(len(sent_words), len(existing_words))
                    if (sent_words or existing_words)
                    else 0
                )

                if overlap > threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_sentences.append(sent)

        return unique_sentences
