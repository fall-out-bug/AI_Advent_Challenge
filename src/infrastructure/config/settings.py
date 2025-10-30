"""Application settings and configuration accessors.

Uses pydantic-settings to load environment variables with sensible defaults.
"""

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration settings for the application.

    Purpose:
        Provide typed access to environment-driven configuration values with
        defaults suitable for local development.

    Attributes:
        mongodb_url: Connection URL for MongoDB instance.
        db_name: Default MongoDB database name.
        mongo_timeout_ms: Connection timeout in milliseconds.
    """

    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string",
    )
    db_name: str = Field(default="butler", description="Primary database name")
    mongo_timeout_ms: int = Field(default=10000, description="Mongo client timeout")
    # LLM settings
    llm_url: str = Field(default="", description="LLM service URL (e.g., http://mistral-chat:8000)")
    llm_model: str = Field(default="mistral-7b-instruct-v0.2", description="LLM model name")
    llm_temperature: float = Field(default=0.2, description="Default generation temperature")
    llm_max_tokens: int = Field(default=512, description="Max tokens for LLM generation")
    # Date parsing settings
    default_timezone: str = Field(default="UTC", description="Default timezone")
    default_locale: str = Field(default="en", description="Default locale for date parsing")
    # Schedule settings
    morning_summary_time: str = Field(default="09:00", description="Morning summary time (HH:MM)")
    evening_digest_time: str = Field(default="20:00", description="Evening digest time (HH:MM)")
    quiet_hours_start: int = Field(default=22, description="Quiet hours start (0-23)")
    quiet_hours_end: int = Field(default=8, description="Quiet hours end (0-23)")
    # Debug settings
    debug_notification_interval_minutes: int = Field(default=0, description="Debug mode: send notifications every N minutes (0 = disabled)")
    # Digest summarization settings
    digest_summary_sentences: int = Field(default=8, description="Number of sentences per channel in digest")
    digest_max_channels: int = Field(default=10, description="Maximum channels to show in digest")
    digest_summary_max_chars: int = Field(default=2000, description="Maximum characters per channel summary (Telegram limit is 4096)")
    summarizer_language: str = Field(default="ru", description="Language for summaries (ru/en)")
    summarizer_temperature: float = Field(default=0.5, description="Temperature for summarization (higher = more creative)")
    summarizer_max_tokens: int = Field(default=1200, description="Max tokens for summarization (more = longer summaries)")
    # FSM conversation settings
    conversation_timeout_minutes: int = Field(default=5, description="Timeout in minutes for abandoned FSM conversations")
    max_clarification_attempts: int = Field(default=3, description="Maximum clarification questions before giving up")
    enable_context_aware_parsing: bool = Field(default=True, description="Use conversation context for intent parsing")
    # Post fetcher settings
    post_fetch_interval_hours: int = Field(default=1, description="Post collection frequency in hours")
    post_ttl_days: int = Field(default=7, description="Post retention period in days")

    class Config:
        env_prefix = ""
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance.

    Returns:
        Settings: Initialized and cached settings object.
    """

    return Settings()  # type: ignore[call-arg]
