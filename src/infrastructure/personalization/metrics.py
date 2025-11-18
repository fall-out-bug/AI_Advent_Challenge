"""Prometheus metrics for personalization."""

from prometheus_client import Counter, Histogram

# Profile metrics
user_profile_reads_total = Counter(
    "user_profile_reads_total",
    "Total user profile reads from repository",
)

user_profile_writes_total = Counter(
    "user_profile_writes_total",
    "Total user profile writes to repository",
)

# Memory metrics
user_memory_events_total = Counter(
    "user_memory_events_total",
    "Total memory events appended",
    ["role"],  # Labels: user, assistant
)

user_memory_compressions_total = Counter(
    "user_memory_compressions_total",
    "Total memory compressions performed",
    ["status"],  # Labels: success, error
)

user_memory_compression_duration_seconds = Histogram(
    "user_memory_compression_duration_seconds",
    "Memory compression duration in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

# Use case metrics
personalized_requests_total = Counter(
    "personalized_requests_total",
    "Total personalized requests",
    ["source", "status"],  # Labels: source (text/voice), status (success/error)
)

personalized_prompt_tokens_total = Histogram(
    "personalized_prompt_tokens_total",
    "Personalized prompt token count",
    buckets=[100, 500, 1000, 1500, 2000, 2500, 3000],
)

# Interest extraction metrics
interest_extraction_total = Counter(
    "interest_extraction_total",
    "Total interest extraction operations",
    ["status"],  # Labels: success, parse_error, llm_error
)

interest_extraction_duration_seconds = Histogram(
    "interest_extraction_duration_seconds",
    "Interest extraction operation duration",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

user_interests_updated_total = Counter(
    "user_interests_updated_total",
    "Total user profile interests updates",
)

user_interests_count = Histogram(
    "user_interests_count",
    "Number of interests per user profile",
    buckets=[0, 1, 3, 5, 7, 10],
)
