"""
Configuration for the Model Switching Demo.

This module contains configuration settings for the model switching demo
including model lists, compression algorithms, token stages, and quality thresholds.
"""

from typing import Dict, List, Any

# Demo configuration
DEMO_CONFIG = {
    # Models to test (each model uses itself for all operations)
    "models": ["starcoder", "mistral", "qwen", "tinyllama"],
    
    # Supported compression algorithms (only truncation and keywords are implemented)
    "compression_algorithms": [
        "truncation",
        "keywords"
    ],
    
    # Token stages for three-stage testing (much larger queries)
    "token_stages": {
        "short": {"min": 500, "max": 1000},      # Still within limits but substantial
        "medium": {"min": 5000, "max": 8000},    # Exceeds StarCoder, within Mistral
        "long": {"min": 15000, "max": 25000}     # Exceeds all current models
    },
    
    # Quality thresholds
    "quality_thresholds": {
        "code_quality_min": 6.0,
        "completeness_min": 0.7,
        "compression_ratio_max": 0.5,
        "response_time_max": 10.0,
        "high_quality_score": 0.8,
        "acceptable_quality_score": 0.6
    },
    
    # Model-specific settings
    "model_settings": {
        "starcoder": {
            "max_tokens": 8192,
            "recommended_input": 7000,
            "temperature": 0.7,
            "max_output_tokens": 1000,
            "complexity_multiplier": 1.0
        },
        "mistral": {
            "max_tokens": 32768,
            "recommended_input": 30000,
            "temperature": 0.7,
            "max_output_tokens": 2000,
            "complexity_multiplier": 0.8
        },
        "qwen": {
            "max_tokens": 32768,
            "recommended_input": 30000,
            "temperature": 0.7,
            "max_output_tokens": 2000,
            "complexity_multiplier": 0.9
        },
        "tinyllama": {
            "max_tokens": 2048,
            "recommended_input": 1500,
            "temperature": 0.7,
            "max_output_tokens": 500,
            "complexity_multiplier": 0.5
        }
    },
    
    # Experiment settings
    "experiment_settings": {
        "max_retries": 3,
        "timeout_seconds": 30,
        "parallel_requests": False,  # Set to True for parallel testing
        "save_intermediate_results": True,
        "detailed_logging": True
    },
    
    # Report settings
    "report_settings": {
        "include_raw_responses": False,  # Set to True for debugging
        "max_response_length": 500,
        "include_charts": True,
        "include_recommendations": True,
        "save_format": "markdown"
    },
    
    # Container management settings
    "container_management": {
        "enabled": True,
        "sequential_switching": True,  # Stop previous before starting next
        "health_check_timeout": 60,
        "health_poll_interval": 2.0,
        "max_health_attempts": 30,
        "start_retry_attempts": 3,
        "start_retry_base_delay": 2.0,
        "stop_timeout": 30
    },
    
    # Demo display configuration
    "demo_display": {
        "step_delay": 2.0,              # Delay between major steps in seconds
        "show_query_preview": 200,      # Characters of query to show
        "show_response_preview": 500,    # Characters of response to show
        "show_full_compression": True,  # Show all compression details
        "pause_between_models": 3.0,    # Delay when switching models
        "verbose_output": True          # Show all details
    },
    
    # Coding task templates
    "task_templates": {
        "short": {
            "description": "Write a Python function to calculate fibonacci number",
            "requirements": [
                "Function name: fibonacci",
                "Input: integer n",
                "Output: fibonacci number",
                "Handle edge cases",
                "Include type hints and docstring"
            ]
        },
        "medium": {
            "description": "Implement a binary search tree with insert, search, delete operations",
            "requirements": [
                "Class name: BinarySearchTree",
                "Node class: BSTNode",
                "Methods: insert, search, delete, inorder_traversal",
                "Include proper documentation",
                "Handle edge cases",
                "Add type hints"
            ]
        },
        "long": {
            "description": "Implement a comprehensive REST API server using FastAPI",
            "requirements": [
                "Use FastAPI framework",
                "Database integration with SQLAlchemy",
                "JWT authentication",
                "User management endpoints",
                "Product management endpoints",
                "Order management endpoints",
                "Comprehensive error handling",
                "API documentation",
                "Testing setup",
                "Docker containerization"
            ]
        }
    }
}

# Model availability check settings
MODEL_CHECK_CONFIG = {
    "check_timeout": 5,  # seconds
    "retry_attempts": 3,
    "retry_delay": 1,  # seconds
    "health_check_endpoint": "/health",
    "required_models": ["starcoder", "mistral"]
}

# Compression algorithm priorities (for fallback)
COMPRESSION_PRIORITIES = [
    "truncation",      # Most reliable
    "keywords",        # Good for code
    "extractive",      # Good for documentation
    "semantic",        # Advanced but may fail
    "summarization"    # Most advanced but slowest
]

# Quality evaluation weights
QUALITY_WEIGHTS = {
    "performance": 0.3,
    "code_quality": 0.4,
    "completeness": 0.2,
    "compression_efficiency": 0.1
}

# Performance benchmarks
PERFORMANCE_BENCHMARKS = {
    "excellent_response_time": 2.0,  # seconds
    "good_response_time": 5.0,      # seconds
    "acceptable_response_time": 10.0, # seconds
    "excellent_tokens_per_second": 100,
    "good_tokens_per_second": 50,
    "acceptable_tokens_per_second": 20
}

def get_config() -> Dict[str, Any]:
    """
    Get the complete demo configuration.
    
    Returns:
        Dictionary containing all configuration settings
        
    Example:
        ```python
        from config.demo_config import get_config
        
        config = get_config()
        models = config["models"]
        print(f"Testing models: {models}")
        ```
    """
    return DEMO_CONFIG.copy()

def get_model_config(model_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Dictionary containing model-specific settings
        
    Example:
        ```python
        from config.demo_config import get_model_config
        
        starcoder_config = get_model_config("starcoder")
        print(f"Max tokens: {starcoder_config['max_tokens']}")
        ```
    """
    return DEMO_CONFIG["model_settings"].get(model_name, {})

def get_quality_thresholds() -> Dict[str, Any]:
    """
    Get quality thresholds configuration.
    
    Returns:
        Dictionary containing quality thresholds
        
    Example:
        ```python
        from config.demo_config import get_quality_thresholds
        
        thresholds = get_quality_thresholds()
        min_quality = thresholds["code_quality_min"]
        print(f"Minimum quality score: {min_quality}")
        ```
    """
    return DEMO_CONFIG["quality_thresholds"].copy()

def get_compression_algorithms() -> List[str]:
    """
    Get list of available compression algorithms.
    
    Returns:
        List of compression algorithm names
        
    Example:
        ```python
        from config.demo_config import get_compression_algorithms
        
        algorithms = get_compression_algorithms()
        print(f"Available algorithms: {algorithms}")
        ```
    """
    return DEMO_CONFIG["compression_algorithms"].copy()

def get_task_template(stage: str) -> Dict[str, Any]:
    """
    Get task template for a specific stage.
    
    Args:
        stage: Stage name (short/medium/long)
        
    Returns:
        Dictionary containing task template
        
    Example:
        ```python
        from config.demo_config import get_task_template
        
        short_task = get_task_template("short")
        print(f"Description: {short_task['description']}")
        ```
    """
    return DEMO_CONFIG["task_templates"].get(stage, {})

def is_model_supported(model_name: str) -> bool:
    """
    Check if a model is supported in the demo.
    
    Args:
        model_name: Name of the model
        
    Returns:
        True if model is supported, False otherwise
        
    Example:
        ```python
        from config.demo_config import is_model_supported
        
        if is_model_supported("starcoder"):
            print("StarCoder is supported")
        ```
    """
    return model_name in DEMO_CONFIG["models"]

def get_experiment_settings() -> Dict[str, Any]:
    """
    Get experiment settings configuration.
    
    Returns:
        Dictionary containing experiment settings
        
    Example:
        ```python
        from config.demo_config import get_experiment_settings
        
        settings = get_experiment_settings()
        max_retries = settings["max_retries"]
        print(f"Max retries: {max_retries}")
        ```
    """
    return DEMO_CONFIG["experiment_settings"].copy()

def get_container_management_settings() -> Dict[str, Any]:
    """
    Get container management settings configuration.
    
    Returns:
        Dictionary containing container management settings
        
    Example:
        ```python
        from config.demo_config import get_container_management_settings
        
        settings = get_container_management_settings()
        enabled = settings["enabled"]
        print(f"Container management enabled: {enabled}")
        ```
    """
    return DEMO_CONFIG["container_management"].copy()
