"""HW Checker infrastructure module.

HTTP client for HW Checker MCP API integration.
Following Python Zen: Simple is better than complex.
"""

from src.infrastructure.hw_checker.client import HWCheckerClient

__all__ = ["HWCheckerClient"]
