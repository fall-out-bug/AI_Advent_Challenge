"""Configuration management for MCP module."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class MCPConfig:
    """Configuration for MCP operations."""

    # Default models
    generation_model: str
    review_model: str
    generation_fallback: list[str]
    review_fallback: list[str]

    # Timeouts (seconds)
    tool_discovery_timeout: float
    tool_execution_timeout: float
    model_check_timeout: float
    workflow_timeout: float

    # Retry settings
    retry_enabled: bool
    retry_max_attempts: int
    retry_initial_delay: float
    retry_backoff_factor: float
    retry_max_delay: float

    # Logging
    log_level: str
    log_format: str
    log_tool_calls: bool
    log_tool_results: bool

    # Performance
    cache_enabled: bool
    cache_ttl: int
    max_concurrent_requests: int

    # Validation
    strict_mode: bool
    max_description_length: int
    max_code_length: int
    max_token_text_length: int

    # Features
    streaming: bool
    telemetry: bool
    resource_endpoints: bool
    prompt_templates: bool
    tool_versioning: bool

    @classmethod
    def load(cls, config_path: str | None = None) -> "MCPConfig":
        """Load configuration from file and environment.

        Args:
            config_path: Path to config file (defaults to config/mcp_config.yaml)

        Returns:
            MCPConfig instance
        """
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent / "config" / "mcp_config.yaml"
            )

        config_data = cls._load_yaml(config_path)
        mcp_config = config_data.get("mcp", {})

        defaults = mcp_config.get("defaults", {})
        timeouts = mcp_config.get("timeouts", {})
        retry = mcp_config.get("retry", {})
        logging = mcp_config.get("logging", {})
        performance = mcp_config.get("performance", {})
        validation = mcp_config.get("validation", {})
        features = mcp_config.get("features", {})

        return cls(
            generation_model=cls._env_or_default(
                "MCP_GENERATION_MODEL", defaults.get("generation_model", "mistral")
            ),
            review_model=cls._env_or_default(
                "MCP_REVIEW_MODEL", defaults.get("review_model", "mistral")
            ),
            generation_fallback=defaults.get(
                "generation_fallback", ["mistral", "qwen"]
            ),
            review_fallback=defaults.get("review_fallback", ["mistral", "qwen"]),
            tool_discovery_timeout=float(timeouts.get("tool_discovery", 5.0)),
            tool_execution_timeout=float(timeouts.get("tool_execution", 30.0)),
            model_check_timeout=float(timeouts.get("model_check", 10.0)),
            workflow_timeout=float(timeouts.get("workflow", 120.0)),
            retry_enabled=retry.get("enabled", True),
            retry_max_attempts=retry.get("max_attempts", 3),
            retry_initial_delay=float(retry.get("initial_delay", 1.0)),
            retry_backoff_factor=float(retry.get("backoff_factor", 2.0)),
            retry_max_delay=float(retry.get("max_delay", 10.0)),
            log_level=logging.get("level", "INFO"),
            log_format=logging.get(
                "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            log_tool_calls=logging.get("log_tool_calls", True),
            log_tool_results=logging.get("log_tool_results", False),
            cache_enabled=performance.get("cache_enabled", False),
            cache_ttl=performance.get("cache_ttl", 3600),
            max_concurrent_requests=performance.get("max_concurrent_requests", 5),
            strict_mode=validation.get("strict_mode", True),
            max_description_length=validation.get("max_description_length", 5000),
            max_code_length=validation.get("max_code_length", 100000),
            max_token_text_length=validation.get("max_token_text_length", 1000000),
            streaming=features.get("streaming", False),
            telemetry=features.get("telemetry", False),
            resource_endpoints=features.get("resource_endpoints", False),
            prompt_templates=features.get("prompt_templates", False),
            tool_versioning=features.get("tool_versioning", False),
        )

    @staticmethod
    def _load_yaml(config_path: str | Path) -> Dict[str, Any]:
        """Load YAML configuration file.

        Args:
            config_path: Path to config file

        Returns:
            Configuration data
        """
        config_path = Path(config_path)
        if not config_path.exists():
            return {}

        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def _env_or_default(env_var: str, default: Any) -> Any:
        """Get value from environment variable or use default.

        Args:
            env_var: Environment variable name
            default: Default value

        Returns:
            Environment variable value or default
        """
        return os.getenv(env_var, default)

    def get_timeout(self, operation: str) -> float:
        """Get timeout for specific operation.

        Args:
            operation: Operation name (discovery, execution, etc.)

        Returns:
            Timeout in seconds
        """
        timeout_map = {
            "discovery": self.tool_discovery_timeout,
            "execution": self.tool_execution_timeout,
            "model_check": self.model_check_timeout,
            "workflow": self.workflow_timeout,
        }
        return timeout_map.get(operation, 30.0)


# Global configuration instance
_config: MCPConfig | None = None


def get_config() -> MCPConfig:
    """Get global MCP configuration.

    Returns:
        Global MCPConfig instance
    """
    global _config
    if _config is None:
        _config = MCPConfig.load()
    return _config


def reload_config() -> MCPConfig:
    """Reload configuration from file.

    Returns:
        New MCPConfig instance
    """
    global _config
    _config = MCPConfig.load()
    return _config
