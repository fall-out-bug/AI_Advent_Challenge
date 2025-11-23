"""Unit tests for OpsSkillAdapter."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.skill_result import SkillResultStatus
from src.domain.god_agent.value_objects.skill import SkillType
from src.infrastructure.god_agent.adapters.ops_skill_adapter import OpsSkillAdapter


@pytest.fixture
def mock_prometheus_client():
    """Mock Prometheus client."""
    client = MagicMock()
    return client


@pytest.fixture
def ops_adapter(mock_prometheus_client):
    """Create OpsSkillAdapter instance."""
    return OpsSkillAdapter(prometheus_url="http://localhost:9090")


@pytest.fixture
def sample_memory_snapshot():
    """Create sample MemorySnapshot."""
    return MemorySnapshot(
        user_id="user_123",
        profile_summary="Persona: Alfred | Language: en",
        conversation_summary="Recent chat",
        rag_hits=[],
        artifact_refs=[],
    )


@pytest.mark.asyncio
async def test_execute_fetches_prometheus_metrics(ops_adapter, sample_memory_snapshot):
    """Test execute fetches Prometheus metrics."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": [
                        {
                            "metric": {"__name__": "test_metric"},
                            "value": [1234567890, "42"],
                        }
                    ],
                },
            }
        )
        mock_get.return_value.__aenter__.return_value = mock_response

        input_data = {"action": "metrics", "query": "up"}
        result = await ops_adapter.execute(input_data, sample_memory_snapshot)

        assert result.status == SkillResultStatus.SUCCESS
        assert result.output is not None
        assert "metrics" in result.output


@pytest.mark.asyncio
async def test_execute_handles_prometheus_error(ops_adapter, sample_memory_snapshot):
    """Test execute handles Prometheus errors."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_get.return_value.__aenter__.return_value = mock_response

        input_data = {"action": "metrics", "query": "up"}
        result = await ops_adapter.execute(input_data, sample_memory_snapshot)

        assert result.status == SkillResultStatus.FAILURE
        assert result.error is not None


@pytest.mark.asyncio
async def test_get_skill_id_returns_ops(
    ops_adapter,
):
    """Test get_skill_id returns ops."""
    skill_id = ops_adapter.get_skill_id()

    assert skill_id == SkillType.OPS.value


@pytest.mark.asyncio
async def test_execute_handles_health_check(ops_adapter, sample_memory_snapshot):
    """Test execute handles health check action."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="OK")
        mock_get.return_value.__aenter__.return_value = mock_response

        input_data = {"action": "health"}
        result = await ops_adapter.execute(input_data, sample_memory_snapshot)

        assert result.status == SkillResultStatus.SUCCESS
        assert result.output is not None
        assert "status" in result.output
