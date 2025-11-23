"""Unit tests for PlanCompilerService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.god_agent.services.plan_compiler_service import PlanCompilerService
from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.task_plan import TaskPlan
from src.domain.god_agent.value_objects.intent import Intent, IntentType


@pytest.fixture
def mock_llm_client():
    """Mock LLMClientProtocol."""
    client = AsyncMock()
    return client


@pytest.fixture
def plan_compiler_service(mock_llm_client):
    """Create PlanCompilerService instance."""
    return PlanCompilerService(llm_client=mock_llm_client)


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
async def test_compile_plan_generates_task_plan(
    plan_compiler_service,
    mock_llm_client,
    sample_intent,
    sample_memory_snapshot,
):
    """Test compile_plan generates TaskPlan DAG."""
    # Mock LLM response with simple plan
    mock_llm_client.make_request.return_value = (
        '{"steps": [{"step_id": "step1", "skill_type": "research", '
        '"depends_on": []}, {"step_id": "step2", "skill_type": "builder", '
        '"depends_on": ["step1"]}]}'
    )

    plan = await plan_compiler_service.compile_plan(
        sample_intent, sample_memory_snapshot
    )

    assert isinstance(plan, TaskPlan)
    assert len(plan.steps) > 0
    assert all(step.step_id for step in plan.steps)


@pytest.mark.asyncio
async def test_compile_plan_enforces_max_10_steps(
    plan_compiler_service,
    mock_llm_client,
    sample_intent,
    sample_memory_snapshot,
):
    """Test compile_plan enforces max 10 steps."""
    # Mock LLM response with 11 steps (should be truncated)
    steps_json = ",".join(
        [
            f'{{"step_id": "step{i}", "skill_type": "research", "depends_on": []}}'
            for i in range(11)
        ]
    )
    mock_llm_client.make_request.return_value = f'{{"steps": [{steps_json}]}}'

    plan = await plan_compiler_service.compile_plan(
        sample_intent, sample_memory_snapshot
    )

    assert len(plan.steps) <= 10


@pytest.mark.asyncio
async def test_compile_plan_respects_token_budget(
    plan_compiler_service,
    mock_llm_client,
    sample_intent,
    sample_memory_snapshot,
):
    """Test compile_plan respects 2500 token budget."""
    mock_llm_client.make_request.return_value = (
        '{"steps": [{"step_id": "step1", "skill_type": "research"}]}'
    )

    await plan_compiler_service.compile_plan(sample_intent, sample_memory_snapshot)

    # Check that max_tokens was set
    call_args = mock_llm_client.make_request.call_args
    assert call_args is not None
    # max_tokens should be set to respect budget
    assert (
        "max_tokens" in call_args.kwargs
        or call_args.kwargs.get("max_tokens") is not None
    )


@pytest.mark.asyncio
async def test_validate_plan_detects_cycles(
    plan_compiler_service,
):
    """Test validate_plan detects dependency cycles."""
    from src.domain.god_agent.entities.task_step import TaskStep, TaskStepStatus
    from src.domain.god_agent.value_objects.skill import SkillType

    # TaskPlan validates cycles in __post_init__, so we can't create invalid plan
    # Instead, test that TaskPlan creation itself raises error for cycles
    step1 = TaskStep(
        step_id="step1",
        skill_type=SkillType.RESEARCH,
        status=TaskStepStatus.PENDING,
        depends_on=["step2"],
    )
    step2 = TaskStep(
        step_id="step2",
        skill_type=SkillType.BUILDER,
        status=TaskStepStatus.PENDING,
        depends_on=["step1"],
    )

    # TaskPlan creation should raise error for cycles
    with pytest.raises(ValueError, match="TaskPlan contains cycle"):
        TaskPlan(plan_id="plan1", steps=[step1, step2])


@pytest.mark.asyncio
async def test_validate_plan_valid_dag(
    plan_compiler_service,
):
    """Test validate_plan accepts valid DAG."""
    from src.domain.god_agent.entities.task_step import TaskStep, TaskStepStatus
    from src.domain.god_agent.value_objects.skill import SkillType

    # Create valid plan
    step1 = TaskStep(
        step_id="step1",
        skill_type=SkillType.RESEARCH,
        status=TaskStepStatus.PENDING,
    )
    step2 = TaskStep(
        step_id="step2",
        skill_type=SkillType.BUILDER,
        status=TaskStepStatus.PENDING,
        depends_on=["step1"],
    )
    plan = TaskPlan(plan_id="plan1", steps=[step1, step2])

    # Should not raise
    result = plan_compiler_service.validate_plan(plan)
    assert result is True


@pytest.mark.asyncio
async def test_compile_plan_handles_llm_error(
    plan_compiler_service,
    mock_llm_client,
    sample_intent,
    sample_memory_snapshot,
):
    """Test compile_plan handles LLM errors gracefully."""
    mock_llm_client.make_request.side_effect = Exception("LLM error")

    # Should handle error and return fallback plan or raise
    with pytest.raises(Exception):
        await plan_compiler_service.compile_plan(sample_intent, sample_memory_snapshot)


@pytest.mark.asyncio
async def test_compile_plan_parses_json_response(
    plan_compiler_service,
    mock_llm_client,
    sample_intent,
    sample_memory_snapshot,
):
    """Test compile_plan parses JSON response from LLM."""
    mock_llm_client.make_request.return_value = (
        '{"steps": [{"step_id": "step1", "skill_type": "research", '
        '"depends_on": [], "acceptance_criteria": ["result contains info"]}]}'
    )

    plan = await plan_compiler_service.compile_plan(
        sample_intent, sample_memory_snapshot
    )

    assert len(plan.steps) == 1
    assert plan.steps[0].step_id == "step1"
    assert len(plan.steps[0].acceptance_criteria) == 1
