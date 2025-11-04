"""Tests for HWCheckerClient.

Following TDD approach with comprehensive test coverage.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import Response, HTTPStatusError, RequestError

from src.infrastructure.hw_checker.client import HWCheckerClient


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient for testing.

    Returns:
        Mocked httpx AsyncClient
    """
    mock_client = AsyncMock()
    return mock_client


@pytest.fixture
def hw_checker_client(mock_httpx_client):
    """Create HWCheckerClient with mocked httpx client.

    Args:
        mock_httpx_client: Mocked httpx AsyncClient

    Returns:
        HWCheckerClient instance
    """
    with patch("src.infrastructure.hw_checker.client.httpx.AsyncClient") as mock_client_class:
        mock_client_class.return_value = mock_httpx_client
        client = HWCheckerClient(base_url="http://test-server:8005", timeout=30.0)
        client.client = mock_httpx_client
        return client


@pytest.mark.asyncio
class TestHWCheckerClientGetRecentCommits:
    """Test suite for get_recent_commits method."""

    async def test_get_recent_commits_success(self, hw_checker_client, mock_httpx_client):
        """Test successful get_recent_commits call.

        Args:
            hw_checker_client: HWCheckerClient instance
            mock_httpx_client: Mocked httpx AsyncClient
        """
        # Arrange
        expected_response = {
            "commits": [
                {
                    "commit_hash": "abc123",
                    "archive_name": "test_hw2.zip",
                    "commit_dttm": "2024-11-02T16:00:00",
                    "assignment": "HW2",
                    "status": "passed",
                }
            ],
            "total": 1,
        }
        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        # Act
        result = await hw_checker_client.get_recent_commits(days=1)

        # Assert
        assert result == expected_response
        mock_httpx_client.get.assert_called_once()
        call_args = mock_httpx_client.get.call_args
        assert "/api/recent_commits" in call_args[0][0]
        assert call_args[1]["params"]["days"] == 1

    async def test_get_recent_commits_with_assignment(
        self, hw_checker_client, mock_httpx_client
    ):
        """Test get_recent_commits with assignment filter.

        Args:
            hw_checker_client: HWCheckerClient instance
            mock_httpx_client: Mocked httpx AsyncClient
        """
        # Arrange
        expected_response = {"commits": [], "total": 0}
        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        # Act
        result = await hw_checker_client.get_recent_commits(days=7, assignment="HW2")

        # Assert
        assert result == expected_response
        call_args = mock_httpx_client.get.call_args
        assert call_args[1]["params"]["days"] == 7
        assert call_args[1]["params"]["assignment"] == "HW2"

    async def test_get_recent_commits_http_error(
        self, hw_checker_client, mock_httpx_client
    ):
        """Test get_recent_commits with HTTP error.

        Args:
            hw_checker_client: HWCheckerClient instance
            mock_httpx_client: Mocked httpx AsyncClient
        """
        # Arrange
        mock_response = MagicMock(spec=Response)
        mock_response.raise_for_status.side_effect = HTTPStatusError(
            "404", request=MagicMock(), response=mock_response
        )
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        # Act & Assert
        with pytest.raises(HTTPStatusError):
            await hw_checker_client.get_recent_commits()

    async def test_get_recent_commits_request_error(
        self, hw_checker_client, mock_httpx_client
    ):
        """Test get_recent_commits with request error.

        Args:
            hw_checker_client: HWCheckerClient instance
            mock_httpx_client: Mocked httpx AsyncClient
        """
        # Arrange
        mock_httpx_client.get = AsyncMock(side_effect=RequestError("Connection failed"))

        # Act & Assert
        with pytest.raises(RequestError):
            await hw_checker_client.get_recent_commits()


@pytest.mark.asyncio
class TestHWCheckerClientDownloadArchive:
    """Test suite for download_archive method."""

    async def test_download_archive_success(self, hw_checker_client, mock_httpx_client):
        """Test successful download_archive call.

        Args:
            hw_checker_client: HWCheckerClient instance
            mock_httpx_client: Mocked httpx AsyncClient
        """
        # Arrange
        commit_hash = "abc123def456"
        expected_content = b"PK\x03\x04fake zip content"
        mock_response = MagicMock(spec=Response)
        mock_response.content = expected_content
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        # Act
        result = await hw_checker_client.download_archive(commit_hash)

        # Assert
        assert result == expected_content
        mock_httpx_client.get.assert_called_once()
        call_args = mock_httpx_client.get.call_args
        assert f"/api/archive/{commit_hash}/download" in call_args[0][0]

    async def test_download_archive_with_assignment(
        self, hw_checker_client, mock_httpx_client
    ):
        """Test download_archive with assignment filter.

        Args:
            hw_checker_client: HWCheckerClient instance
            mock_httpx_client: Mocked httpx AsyncClient
        """
        # Arrange
        commit_hash = "abc123"
        expected_content = b"PK\x03\x04"
        mock_response = MagicMock(spec=Response)
        mock_response.content = expected_content
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        # Act
        result = await hw_checker_client.download_archive(commit_hash, assignment="HW2")

        # Assert
        assert result == expected_content
        call_args = mock_httpx_client.get.call_args
        assert call_args[1]["params"]["assignment"] == "HW2"

    async def test_download_archive_http_error(
        self, hw_checker_client, mock_httpx_client
    ):
        """Test download_archive with HTTP error.

        Args:
            hw_checker_client: HWCheckerClient instance
            mock_httpx_client: Mocked httpx AsyncClient
        """
        # Arrange
        commit_hash = "abc123"
        mock_response = MagicMock(spec=Response)
        mock_response.raise_for_status.side_effect = HTTPStatusError(
            "404", request=MagicMock(), response=mock_response
        )
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        # Act & Assert
        with pytest.raises(HTTPStatusError):
            await hw_checker_client.download_archive(commit_hash)

    async def test_download_archive_request_error(
        self, hw_checker_client, mock_httpx_client
    ):
        """Test download_archive with request error.

        Args:
            hw_checker_client: HWCheckerClient instance
            mock_httpx_client: Mocked httpx AsyncClient
        """
        # Arrange
        commit_hash = "abc123"
        mock_httpx_client.get = AsyncMock(side_effect=RequestError("Connection failed"))

        # Act & Assert
        with pytest.raises(RequestError):
            await hw_checker_client.download_archive(commit_hash)


@pytest.mark.asyncio
class TestHWCheckerClientClose:
    """Test suite for close method."""

    async def test_close_success(self, hw_checker_client, mock_httpx_client):
        """Test successful client close.

        Args:
            hw_checker_client: HWCheckerClient instance
            mock_httpx_client: Mocked httpx AsyncClient
        """
        # Arrange
        mock_httpx_client.aclose = AsyncMock()

        # Act
        await hw_checker_client.close()

        # Assert
        mock_httpx_client.aclose.assert_called_once()

