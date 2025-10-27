"""
Tests for Docker manager functionality.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from utils.docker_manager import ModelDockerManager


@pytest.fixture
def mock_docker_client():
    """Create mock Docker client."""
    client = Mock()
    return client


@pytest.fixture
def docker_manager(mock_docker_client):
    """Create ModelDockerManager with mocked Docker client."""
    with patch("utils.docker_manager.docker.from_env", return_value=mock_docker_client):
        return ModelDockerManager()


def test_get_running_models(docker_manager, mock_docker_client):
    """Test getting list of running models."""
    # Mock container list
    mock_container1 = Mock()
    mock_container1.name = "local_models-starcoder-chat-1"

    mock_container2 = Mock()
    mock_container2.name = "local_models-mistral-chat-1"

    mock_docker_client.containers.list.return_value = [mock_container1, mock_container2]

    models = docker_manager.get_running_models()

    assert "starcoder" in models
    assert "mistral" in models
    assert len(models) == 2


def test_get_container_name(docker_manager):
    """Test container name generation."""
    name = docker_manager.get_container_name("starcoder")
    assert name == "local_models-starcoder-chat-1"


@pytest.mark.asyncio
async def test_stop_model_success(docker_manager, mock_docker_client):
    """Test successful model stopping."""
    mock_container = Mock()
    mock_docker_client.containers.get.return_value = mock_container

    result = await docker_manager.stop_model("starcoder")

    assert result is True
    mock_container.stop.assert_called_once_with(timeout=30)


@pytest.mark.asyncio
async def test_stop_model_not_found(docker_manager, mock_docker_client):
    """Test stopping non-existent model."""
    from docker.errors import NotFound

    mock_docker_client.containers.get.side_effect = NotFound("Container not found")

    result = await docker_manager.stop_model("nonexistent")

    assert result is False


@pytest.mark.asyncio
async def test_start_model_success(docker_manager, mock_docker_client):
    """Test successful model starting."""
    mock_container = Mock()
    mock_container.status = "running"
    mock_docker_client.containers.get.return_value = mock_container

    result = await docker_manager.start_model("starcoder")

    assert result is True
    mock_container.start.assert_called_once()


@pytest.mark.asyncio
async def test_start_model_not_found(docker_manager, mock_docker_client):
    """Test starting non-existent model."""
    from docker.errors import NotFound

    mock_docker_client.containers.get.side_effect = NotFound("Container not found")

    result = await docker_manager.start_model("nonexistent")

    assert result is False


@pytest.mark.asyncio
async def test_swap_models(docker_manager, mock_docker_client):
    """Test swapping between models."""
    mock_container = Mock()
    mock_container.status = "running"
    mock_docker_client.containers.get.return_value = mock_container

    result = await docker_manager.swap_models("starcoder", "mistral")

    assert result["stopped"] is True
    assert result["started"] is True


@pytest.mark.asyncio
async def test_ensure_model_running_already_running(docker_manager, mock_docker_client):
    """Test ensuring model is running when already running."""
    mock_container = Mock()
    mock_container.status = "running"
    mock_docker_client.containers.get.return_value = mock_container

    result = await docker_manager.ensure_model_running("starcoder")

    assert result is True


def test_get_container_status(docker_manager, mock_docker_client):
    """Test getting container status."""
    mock_container = Mock()
    mock_container.status = "running"
    mock_docker_client.containers.get.return_value = mock_container

    status = docker_manager.get_container_status("starcoder")

    assert status == "running"


def test_get_container_status_not_found(docker_manager, mock_docker_client):
    """Test getting status of non-existent container."""
    from docker.errors import NotFound

    mock_docker_client.containers.get.side_effect = NotFound("Container not found")

    status = docker_manager.get_container_status("nonexistent")

    assert status is None


@pytest.mark.asyncio
async def test_cleanup_stopped_containers(docker_manager, mock_docker_client):
    """Test cleaning up stopped containers."""
    mock_container = Mock()
    mock_container.name = "local_models-starcoder-chat-1"
    mock_docker_client.containers.list.return_value = [mock_container]

    cleaned = await docker_manager.cleanup_stopped_containers()

    assert cleaned == 1
    mock_container.remove.assert_called_once()
