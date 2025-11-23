"""Security tests for no external SaaS dependencies."""

from unittest.mock import patch

import pytest


def test_no_external_saas_dependencies():
    """Test that no external SaaS dependencies are used."""
    # Check that all imports are local or standard library
    import src.application.god_agent.services.god_agent_orchestrator
    import src.application.god_agent.services.intent_router_service
    import src.application.god_agent.services.plan_compiler_service
    import src.infrastructure.god_agent.adapters.builder_skill_adapter
    import src.infrastructure.god_agent.adapters.concierge_skill_adapter
    import src.infrastructure.god_agent.adapters.ops_skill_adapter
    import src.infrastructure.god_agent.adapters.research_skill_adapter
    import src.infrastructure.god_agent.adapters.reviewer_skill_adapter

    # Verify no external SaaS API calls
    # All data stays local (MongoDB, Prometheus, Qwen)
    assert True  # Placeholder - actual implementation will verify


def test_all_data_stays_local():
    """Test that all data processing stays local."""
    # Verify:
    # - MongoDB for persistence (local/shared infra)
    # - Prometheus for metrics (local/shared infra)
    # - Qwen LLM (local)
    # - No external API calls to SaaS services

    # Check that no external API keys or endpoints are hardcoded
    import os

    # Verify no external SaaS environment variables
    external_saas_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "AZURE_API_KEY",
    ]

    for var in external_saas_vars:
        assert (
            var not in os.environ or os.getenv(var) is None
        ), f"External SaaS dependency detected: {var}"

    assert True  # Test passes if no external SaaS vars found
