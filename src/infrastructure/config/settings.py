"""Application settings and configuration accessors.

Uses pydantic-settings to load environment variables with sensible defaults.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
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
    storage_path: Path = Field(
        default=Path("/tmp/ai_challenge"),
        description="Base directory for storing persistent runtime files",
    )
    # LLM settings
    llm_url: str = Field(
        default="", description="LLM service URL (e.g., http://mistral-chat:8000)"
    )
    llm_model: str = Field(
        default="mistral-7b-instruct-v0.2", description="LLM model name"
    )
    llm_temperature: float = Field(
        default=0.2, description="Default generation temperature"
    )
    llm_max_tokens: int = Field(
        default=512, description="Max tokens for LLM generation"
    )
    # Date parsing settings
    default_timezone: str = Field(default="UTC", description="Default timezone")
    default_locale: str = Field(
        default="en", description="Default locale for date parsing"
    )
    # Schedule settings
    morning_summary_time: str = Field(
        default="09:00", description="Morning summary time (HH:MM)"
    )
    evening_digest_time: str = Field(
        default="20:00", description="Evening digest time (HH:MM)"
    )
    quiet_hours_start: int = Field(default=22, description="Quiet hours start (0-23)")
    quiet_hours_end: int = Field(default=8, description="Quiet hours end (0-23)")
    # Debug settings
    debug_notification_interval_minutes: int = Field(
        default=0,
        description="Debug mode: send notifications every N minutes (0 = disabled)",
    )
    # Digest summarization settings
    digest_summary_sentences: int = Field(
        default=25, description="Number of sentences per channel in digest"
    )
    digest_max_channels: int = Field(
        default=10, description="Maximum channels to show in digest"
    )
    digest_summary_max_chars: int = Field(
        default=3500,
        description="Maximum characters per channel summary (Telegram limit is 4096)",
    )

    # Evaluation settings
    enable_quality_evaluation: bool = Field(
        default=True, description="Enable automatic quality evaluation of summaries"
    )
    evaluation_min_score_for_dataset: float = Field(
        default=0.7, description="Minimum score to include in fine-tuning dataset"
    )
    benchmark_dataset_dir: Path = Field(
        default=Path("data/benchmarks"),
        description="Base directory containing benchmark datasets",
    )
    benchmark_max_concurrency: int = Field(
        default=4,
        description="Maximum concurrent LLM judge requests during benchmark runs",
    )
    benchmark_judge_timeout_seconds: float = Field(
        default=180.0,
        description="Timeout applied to LLM judge calls within benchmark runs",
    )

    # Fine-tuning settings
    enable_auto_finetuning: bool = Field(
        default=True, description="Enable automatic fine-tuning when threshold reached"
    )
    finetuning_min_samples: int = Field(
        default=100,
        description="Minimum number of high-quality samples to trigger fine-tuning",
    )
    finetuning_model_output_dir: str = Field(
        default="/models/fine_tuned",
        description="Base directory for storing fine-tuned models",
    )
    finetuning_base_model: str = Field(
        default="mistralai/Mistral-7B-Instruct-v0.2",
        description="Base model name for fine-tuning",
    )
    finetuning_num_epochs: int = Field(
        default=3, description="Number of training epochs"
    )
    finetuning_batch_size: int = Field(default=4, description="Training batch size")
    finetuning_learning_rate: float = Field(
        default=2e-5, description="Learning rate for fine-tuning"
    )
    summarizer_language: str = Field(
        default="ru", description="Language for summaries (ru/en)"
    )
    summarizer_temperature: float = Field(
        default=0.7,
        description="Temperature for summarization (higher = more creative)",
    )
    summarizer_max_tokens: int = Field(
        default=3000,
        description="Max tokens for summarization (more = longer summaries)",
    )
    summarizer_timeout_seconds: float = Field(
        default=180.0,
        description=(
            "Timeout in seconds for LLM summarization requests "
            "(longer for large texts)"
        ),
    )
    summarizer_timeout_seconds_long: float = Field(
        default=600.0,
        description="Timeout in seconds for long async summarization tasks",
    )
    # Long tasks settings
    long_tasks_poll_interval_seconds: int = Field(
        default=5, description="Polling interval for long tasks worker in seconds"
    )
    long_tasks_max_retries: int = Field(
        default=1, description="Maximum retry attempts for failed long tasks"
    )
    enable_async_long_summarization: bool = Field(
        default=True, description="Enable async long summarization feature"
    )
    # Channel search settings
    bot_api_fallback_enabled: bool = Field(
        default=True,
        description=(
            "Enable Bot API fallback for channel search when dialogs search fails"
        ),
    )
    llm_fallback_enabled: bool = Field(
        default=False,
        description="Enable LLM fallback for ambiguous channel search queries",
    )
    # FSM conversation settings
    conversation_timeout_minutes: int = Field(
        default=5, description="Timeout in minutes for abandoned FSM conversations"
    )
    max_clarification_attempts: int = Field(
        default=3, description="Maximum clarification questions before giving up"
    )
    enable_context_aware_parsing: bool = Field(
        default=True, description="Use conversation context for intent parsing"
    )
    # Post fetcher settings
    post_fetch_interval_hours: int = Field(
        default=1, description="Post collection frequency in hours"
    )
    post_ttl_days: int = Field(default=7, description="Post retention period in days")
    # PDF digest settings
    pdf_cache_ttl_hours: int = Field(
        default=1, description="PDF cache duration in hours"
    )
    pdf_summary_sentences: int = Field(
        default=5,
        description="Sentences per channel in PDF (separate from text digest)",
    )
    pdf_summary_max_chars: int = Field(
        default=3000, description="Max characters per channel summary in PDF"
    )
    pdf_max_posts_per_channel: int = Field(
        default=100, description="Max posts to summarize per channel"
    )

    # Parser/agent flags
    parser_strict_mode: bool = Field(
        default=False, description="If true, decision parser uses strict JSON-only mode"
    )
    parser_max_attempts: int = Field(
        default=3,
        description="Max attempts when parsing tool call from fragmented text",
    )
    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_format: Optional[str] = Field(
        default=None,
        description="Custom log format string. If None, uses default format.",
    )
    # Intent classification settings
    intent_confidence_threshold: float = Field(
        default=0.7,
        description=(
            "Minimum confidence threshold for rule-based intent classification "
            "(0.0-1.0)"
        ),
    )
    intent_cache_ttl_seconds: int = Field(
        default=300,
        description=(
            "TTL in seconds for intent classification cache "
            "(default: 300 = 5 minutes)"
        ),
    )
    intent_llm_timeout_seconds: float = Field(
        default=5.0,
        description="Timeout in seconds for LLM intent classification requests",
    )
    # Channel resolution settings
    channel_resolution_exact_username_weight: float = Field(
        default=1.0, description="Weight for exact username match in channel resolution"
    )
    channel_resolution_exact_title_weight: float = Field(
        default=0.9, description="Weight for exact title match in channel resolution"
    )
    channel_resolution_prefix_username_weight: float = Field(
        default=0.7,
        description="Weight for prefix username match in channel resolution",
    )
    channel_resolution_prefix_title_weight: float = Field(
        default=0.6, description="Weight for prefix title match in channel resolution"
    )
    channel_resolution_token_overlap_weight: float = Field(
        default=0.5, description="Weight for token overlap match in channel resolution"
    )
    channel_resolution_levenshtein_username_weight: float = Field(
        default=0.4, description="Weight for Levenshtein distance on username"
    )
    channel_resolution_levenshtein_title_weight: float = Field(
        default=0.3, description="Weight for Levenshtein distance on title"
    )
    channel_resolution_description_mention_weight: float = Field(
        default=0.2, description="Weight for description mention match"
    )
    channel_resolution_threshold: float = Field(
        default=0.6, description="Minimum score threshold for channel match (0.0-1.0)"
    )
    channel_discovery_max_candidates: int = Field(
        default=5,
        description="Maximum number of candidates to return for channel discovery",
    )
    enable_llm_rerank: bool = Field(
        default=True,
        description="Enable LLM re-ranking for close matches (scores 0.6-0.8)",
    )
    # Feature flags
    use_new_summarization: bool = Field(
        default=False,
        description="Use refactored summarization system (Phase 6 migration)",
    )
    # Review system settings
    review_llm_timeout: float = Field(
        default=180.0, description="Timeout in seconds for LLM review requests"
    )
    review_max_retries: int = Field(
        default=3, description="Maximum retry attempts for review LLM calls"
    )
    review_rate_limit_window_seconds: int = Field(
        default=3600,
        description="Rolling window size in seconds for review rate limiting",
    )
    review_rate_limit_per_student: int = Field(
        default=5,
        description="Maximum reviews per student within the rate limit window",
    )
    review_rate_limit_per_assignment: int = Field(
        default=50,
        description="Maximum reviews per assignment within the rate limit window",
    )
    # Archive extraction settings
    archive_max_total_size_mb: int = Field(
        default=50, description="Maximum total size of extracted archive in MB"
    )
    archive_allowed_globs: list[str] = Field(
        default_factory=lambda: [
            "*.py",
            "**/*.py",
            "*.ipynb",
            "**/*.ipynb",
            "*.md",
            "**/*.md",
            "*.yml",
            "**/*.yml",
            "*.yaml",
            "**/*.yaml",
            "*.json",
            "**/*.json",
            "*.txt",
            "**/*.txt",
        ],
        description="Allowed file patterns for archive extraction",
    )
    # External API settings
    external_api_url: str = Field(
        default="", description="External API URL for publishing reviews"
    )
    external_api_key: str = Field(
        default="", description="External API key for authentication"
    )
    external_api_timeout: int = Field(
        default=30, description="Timeout in seconds for external API requests"
    )
    external_api_enabled: bool = Field(
        default=False, description="Enable external API publishing (default: mock only)"
    )
    # Embedding index settings
    embedding_api_url: str = Field(
        default="http://127.0.0.1:11434",
        description="Embedding service base URL (Ollama)",
    )
    embedding_model: str = Field(
        default="nomic-embed-text",
        description="Embedding model identifier",
    )
    embedding_api_timeout_seconds: float = Field(
        default=60.0,
        description="Timeout for embedding API requests",
    )
    embedding_vector_dimension: int = Field(
        default=768,
        description="Expected embedding vector dimension",
    )
    embedding_sources: tuple[str, ...] = Field(
        default=(),
        description="Default filesystem sources for the embedding pipeline",
    )
    embedding_default_language: str = Field(
        default="ru",
        description="Language tag stored with indexed documents",
    )
    embedding_stage_tag: str = Field(
        default="19",
        description="Stage tag stored in metadata for embedding pipeline",
    )
    embedding_max_file_size_mb: int = Field(
        default=20,
        description="Maximum file size (MB) accepted for indexing",
    )
    embedding_batch_size: int = Field(
        default=32,
        description="Number of chunks processed per embedding request",
    )
    embedding_chunk_size_tokens: int = Field(
        default=1200,
        description="Target number of tokens per chunk",
    )
    embedding_chunk_overlap_tokens: int = Field(
        default=200,
        description="Token overlap between adjacent chunks",
    )
    embedding_min_chunk_tokens: int = Field(
        default=200,
        description="Minimum token count for trailing chunks",
    )
    embedding_mongo_database: str = Field(
        default="document_index",
        description="MongoDB database for embedding metadata",
    )
    embedding_mongo_documents_collection: str = Field(
        default="documents",
        description="MongoDB collection for document metadata",
    )
    embedding_mongo_chunks_collection: str = Field(
        default="chunks",
        description="MongoDB collection for document chunks",
    )
    redis_host: str = Field(
        default="127.0.0.1",
        description="Redis host for embedding vector store",
    )
    redis_port: int = Field(
        default=6379,
        description="Redis port for embedding vector store",
    )
    redis_password: str | None = Field(
        default=None,
        description="Redis password for embedding vector store",
    )
    embedding_redis_index_name: str = Field(
        default="embedding:index:v1",
        description="RediSearch index name for embeddings",
    )
    embedding_redis_key_prefix: str = Field(
        default="embedding:chunk:",
        description="Redis key prefix for stored embeddings",
    )
    # Voice/STT settings
    whisper_host: str = Field(
        default="whisper-stt",
        description="Whisper STT service host (default: whisper-stt)",
    )
    whisper_port: int = Field(
        default=8005,
        description="Whisper STT service port (default: 8005)",
    )
    stt_model: str = Field(
        default="base",
        description="Whisper model name (e.g., tiny, base, small, medium, large, large-v2, large-v3)",
    )
    voice_redis_host: str = Field(
        default="shared-redis",
        description="Redis host for voice command store (default: shared-redis)",
    )
    voice_redis_port: int = Field(
        default=6379,
        description="Redis port for voice command store (default: 6379)",
    )
    voice_redis_password: str | None = Field(
        default=None,
        description="Redis password for voice command store (reads from VOICE_REDIS_PASSWORD or REDIS_PASSWORD env var)",
    )
    
    @field_validator("voice_redis_password", mode="before")
    @classmethod
    def validate_voice_redis_password(cls, v: str | None) -> str | None:
        """Validate voice_redis_password by reading from environment if not set."""
        import os
        if v is None:
            # Try VOICE_REDIS_PASSWORD first, then REDIS_PASSWORD as fallback
            v = os.getenv("VOICE_REDIS_PASSWORD") or os.getenv("REDIS_PASSWORD")
        return v
    # RAG retrieval settings
    rag_top_k: int = Field(
        default=5,
        description="Number of chunks to retrieve for RAG",
    )
    rag_score_threshold: float = Field(
        default=0.3,
        description="Minimum similarity score for retrieved chunks",
    )
    rag_max_context_tokens: int = Field(
        default=3000,
        description="Maximum tokens for retrieved context in RAG prompts",
    )
    # HW Checker MCP integration
    hw_checker_mcp_url: str = Field(
        default="http://mcp-server:8005",
        description="Base URL of HW Checker MCP HTTP server",
    )
    hw_checker_mcp_enabled: bool = Field(
        default=True,
        description="Enable publishing via HW Checker MCP server",
    )
    # Review worker settings
    review_worker_poll_interval: int = Field(
        default=5, description="Polling interval in seconds for review worker"
    )
    review_worker_max_backoff: int = Field(
        default=60, description="Maximum backoff delay in seconds when queue is empty"
    )
    # Log analysis settings
    enable_log_analysis: bool = Field(
        default=True, description="Enable runtime log analysis (Pass 4)"
    )
    log_analysis_min_severity: str = Field(
        default="WARNING",
        description="Minimum log severity to analyze (ERROR, WARNING, INFO, DEBUG)",
    )
    log_analysis_max_groups: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of log groups to analyze per submission",
    )
    log_analysis_timeout: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Timeout in seconds for LLM log analysis requests",
    )

    @field_validator("post_fetch_interval_hours")
    @classmethod
    def validate_post_fetch_interval(cls, v: int) -> int:
        """Validate post fetch interval is positive."""
        if v <= 0:
            raise ValueError("post_fetch_interval_hours must be positive")
        return v

    @field_validator("post_ttl_days")
    @classmethod
    def validate_post_ttl(cls, v: int) -> int:
        """Validate post TTL is positive."""
        if v <= 0:
            raise ValueError("post_ttl_days must be positive")
        return v

    @field_validator("pdf_cache_ttl_hours")
    @classmethod
    def validate_pdf_cache_ttl(cls, v: int) -> int:
        """Validate PDF cache TTL is positive."""
        if v <= 0:
            raise ValueError("pdf_cache_ttl_hours must be positive")
        return v

    @field_validator("pdf_summary_sentences")
    @classmethod
    def validate_pdf_summary_sentences(cls, v: int) -> int:
        """Validate PDF summary sentences count is reasonable."""
        if v <= 0:
            raise ValueError("pdf_summary_sentences must be positive")
        if v > 20:
            raise ValueError(
                "pdf_summary_sentences should not exceed 20 for readability"
            )
        return v

    @field_validator("pdf_summary_max_chars")
    @classmethod
    def validate_pdf_summary_max_chars(cls, v: int) -> int:
        """Validate PDF summary max chars is positive."""
        if v <= 0:
            raise ValueError("pdf_summary_max_chars must be positive")
        return v

    @field_validator("pdf_max_posts_per_channel")
    @classmethod
    def validate_pdf_max_posts(cls, v: int) -> int:
        """Validate PDF max posts per channel is positive."""
        if v <= 0:
            raise ValueError("pdf_max_posts_per_channel must be positive")
        return v

    @field_validator("benchmark_max_concurrency")
    @classmethod
    def validate_benchmark_concurrency(cls, value: int) -> int:
        """Validate benchmark concurrency is positive."""
        if value <= 0:
            raise ValueError("benchmark_max_concurrency must be positive")
        return value

    @field_validator("intent_confidence_threshold")
    @classmethod
    def validate_intent_confidence_threshold(cls, v: float) -> float:
        """Validate intent confidence threshold is in valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("intent_confidence_threshold must be between 0.0 and 1.0")
        return v

    @field_validator("intent_cache_ttl_seconds")
    @classmethod
    def validate_intent_cache_ttl(cls, v: int) -> int:
        """Validate intent cache TTL is positive."""
        if v <= 0:
            raise ValueError("intent_cache_ttl_seconds must be positive")
        return v

    @field_validator("intent_llm_timeout_seconds")
    @classmethod
    def validate_intent_llm_timeout(cls, v: float) -> float:
        """Validate intent LLM timeout is positive."""
        if v <= 0:
            raise ValueError("intent_llm_timeout_seconds must be positive")
        return v

    @field_validator("channel_resolution_threshold")
    @classmethod
    def validate_channel_resolution_threshold(cls, v: float) -> float:
        """Validate channel resolution threshold is in valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("channel_resolution_threshold must be between 0.0 and 1.0")
        return v

    @field_validator("channel_discovery_max_candidates")
    @classmethod
    def validate_channel_discovery_max_candidates(cls, v: int) -> int:
        """Validate channel discovery max candidates is positive."""
        if v <= 0:
            raise ValueError("channel_discovery_max_candidates must be positive")
        return v

    @field_validator("review_llm_timeout")
    @classmethod
    def validate_review_llm_timeout(cls, v: float) -> float:
        """Validate review LLM timeout is positive."""
        if v <= 0:
            raise ValueError("review_llm_timeout must be positive")
        return v

    @field_validator("review_max_retries")
    @classmethod
    def validate_review_max_retries(cls, v: int) -> int:
        """Validate review max retries is positive."""
        if v <= 0:
            raise ValueError("review_max_retries must be positive")
        return v

    @field_validator(
        "embedding_max_file_size_mb",
        "embedding_batch_size",
        "embedding_chunk_size_tokens",
        "embedding_min_chunk_tokens",
        "embedding_vector_dimension",
    )
    @classmethod
    def validate_embedding_positive(cls, value: int) -> int:
        """Validate embedding-related integer configuration is positive."""
        if value <= 0:
            raise ValueError("embedding configuration values must be positive")
        return value

    @field_validator("embedding_chunk_overlap_tokens")
    @classmethod
    def validate_embedding_overlap(cls, value: int) -> int:
        """Validate chunk overlap is non-negative."""
        if value < 0:
            raise ValueError("embedding_chunk_overlap_tokens must be non-negative")
        return value

    @field_validator("review_rate_limit_window_seconds")
    @classmethod
    def validate_review_rate_limit_window(cls, v: int) -> int:
        """Validate review rate limit window is positive."""
        if v <= 0:
            raise ValueError("review_rate_limit_window_seconds must be positive")
        return v

    @field_validator("review_rate_limit_per_student")
    @classmethod
    def validate_review_rate_limit_per_student(cls, v: int) -> int:
        """Validate per-student review rate limit is positive."""
        if v <= 0:
            raise ValueError("review_rate_limit_per_student must be positive")
        return v

    @field_validator("review_rate_limit_per_assignment")
    @classmethod
    def validate_review_rate_limit_per_assignment(cls, v: int) -> int:
        """Validate per-assignment review rate limit is positive."""
        if v <= 0:
            raise ValueError("review_rate_limit_per_assignment must be positive")
        return v

    @field_validator("archive_max_total_size_mb")
    @classmethod
    def validate_archive_max_total_size_mb(cls, v: int) -> int:
        """Validate archive max total size is positive."""
        if v <= 0:
            raise ValueError("archive_max_total_size_mb must be positive")
        return v

    @field_validator("external_api_timeout")
    @classmethod
    def validate_external_api_timeout(cls, v: int) -> int:
        """Validate external API timeout is positive."""
        if v <= 0:
            raise ValueError("external_api_timeout must be positive")
        return v

    @field_validator("review_worker_poll_interval")
    @classmethod
    def validate_review_worker_poll_interval(cls, v: int) -> int:
        """Validate review worker poll interval is positive."""
        if v <= 0:
            raise ValueError("review_worker_poll_interval must be positive")
        return v

    @field_validator("review_worker_max_backoff")
    @classmethod
    def validate_review_worker_max_backoff(cls, v: int) -> int:
        """Validate review worker max backoff is positive."""
        if v <= 0:
            raise ValueError("review_worker_max_backoff must be positive")
        return v

    @field_validator("log_analysis_min_severity")
    @classmethod
    def validate_log_analysis_min_severity(cls, v: str) -> str:
        """Validate log analysis min severity is valid."""
        valid_levels = ["ERROR", "WARNING", "INFO", "DEBUG"]
        if v not in valid_levels:
            raise ValueError(f"log_analysis_min_severity must be one of {valid_levels}")
        return v

    @field_validator("log_analysis_timeout")
    @classmethod
    def validate_log_analysis_timeout(cls, v: int) -> int:
        """Validate log analysis timeout is in valid range."""
        if not 10 <= v <= 300:
            raise ValueError("log_analysis_timeout must be between 10 and 300 seconds")
        return v

    class Config:
        env_prefix = ""
        case_sensitive = False

    @classmethod
    def from_env(cls) -> "Settings":
        """Instantiate settings using environment variables."""
        return cls()

    def get_agent_storage_path(self) -> Path:
        """Return path for agent storage."""
        return self.storage_path / "agents"

    def get_experiment_storage_path(self) -> Path:
        """Return path for experiment storage."""
        return self.storage_path / "experiments"

    @property
    def model_default_name(self) -> str:
        """Return default model name (compat shim)."""
        return self.llm_model

    @property
    def model_default_max_tokens(self) -> int:
        """Return default max tokens (compat shim)."""
        return self.llm_max_tokens

    @property
    def model_default_temperature(self) -> float:
        """Return default temperature (compat shim)."""
        return self.llm_temperature


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance.

    Returns:
        Settings: Initialized and cached settings object.
    """

    return Settings()  # type: ignore[call-arg]
