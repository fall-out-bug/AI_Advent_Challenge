"""Prompt templates for intent parsing."""

from __future__ import annotations


def system_prompt() -> str:
    return (
        "You are an intent parser that outputs strict JSON only. "
        "Keys: title, description, deadline (ISO or null), priority (low|medium|high), "
        "tags (list[str]), needs_clarification (bool), questions (list[{text,key}])."
    )


def user_prompt(text: str, context: dict) -> str:
    return f"Text: {text}\nContext: {context}"


