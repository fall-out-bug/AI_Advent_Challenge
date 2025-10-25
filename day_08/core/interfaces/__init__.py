"""
Interfaces module for Token Analysis System.

This module provides Protocol definitions for all major components
to enable dependency injection and SOLID principles.
"""

from .protocols import (
    TokenCounterProtocol,
    CompressorProtocol,
    ModelClientProtocol,
    ReporterProtocol,
    StatisticsCalculatorProtocol,
    ExperimentRunnerProtocol,
    ConfigurationProtocol,
    LoggerProtocol,
    RetryProtocol,
    CircuitBreakerProtocol,
    CacheProtocol,
    ValidatorProtocol,
    FactoryProtocol,
    MetricsProtocol,
)

__all__ = [
    "TokenCounterProtocol",
    "CompressorProtocol", 
    "ModelClientProtocol",
    "ReporterProtocol",
    "StatisticsCalculatorProtocol",
    "ExperimentRunnerProtocol",
    "ConfigurationProtocol",
    "LoggerProtocol",
    "RetryProtocol",
    "CircuitBreakerProtocol",
    "CacheProtocol",
    "ValidatorProtocol",
    "FactoryProtocol",
    "MetricsProtocol",
]
