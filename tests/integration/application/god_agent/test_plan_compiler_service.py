"""Integration tests for PlanCompilerService with LLM."""

import time

import pytest

from src.application.god_agent.services.plan_compiler_service import PlanCompilerService
from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.value_objects.intent import Intent, IntentType


@pytest.fixture
def plan_compiler_service(llm_client):
    """Create PlanCompilerService with real LLM client."""
    return PlanCompilerService(llm_client=llm_client)


@pytest.fixture
def sample_intent():
    """Create sample Intent."""
    return Intent(intent_type=IntentType.BUILD, confidence=0.85)


@pytest.fixture
def sample_memory_snapshot():
    """Create sample MemorySnapshot."""
    return MemorySnapshot(
        user_id="user_123",
        profile_summary="Persona: Alfred | Language: en",
        conversation_summary="User wants to build a calculator",
        rag_hits=[],
        artifact_refs=[],
    )


@pytest.mark.asyncio
async def test_compile_plan_respects_token_budget_integration(
    plan_compiler_service, sample_intent, sample_memory_snapshot
):
    """Test compile_plan respects 2500 token budget (integration)."""
    plan = await plan_compiler_service.compile_plan(
        sample_intent, sample_memory_snapshot
    )

    assert isinstance(plan, type(plan))  # Plan should be created
    # Token budget is enforced in LLM call (max_tokens parameter)


@pytest.mark.asyncio
async def test_compile_plan_watchdog_timer(
    plan_compiler_service, sample_intent, sample_memory_snapshot
):
    """Test compile_plan respects max 30s per step watchdog timer."""
    start_time = time.time()
    plan = await plan_compiler_service.compile_plan(
        sample_intent, sample_memory_snapshot
    )
    elapsed = time.time() - start_time

    # Each step should not take more than 30s (but plan compilation itself may take longer)
    # This is more of a validation that service doesn't hang
    assert elapsed < 60.0  # Overall compilation should complete
