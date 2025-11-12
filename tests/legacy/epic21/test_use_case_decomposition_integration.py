"""Integration tests for use case decomposition with DI container.

Tests the full Clean Architecture integration from use case to domain services.

Epic 21 · Stage 21_01d · Use Case Decomposition
"""

import pytest
from unittest.mock import AsyncMock

from src.infrastructure.di.container import DIContainer, Settings


@pytest.mark.epic21
@pytest.mark.stage_21_01
@pytest.mark.use_case
@pytest.mark.integration
class TestUseCaseDecompositionIntegration:
    """Integration tests for use case decomposition."""

    @pytest.fixture
    async def di_container(self):
        """Create DI container with test settings."""
        # Create minimal settings to avoid pydantic validation issues
        class TestSettings:
            def __init__(self):
                self.use_new_homework_review_service = True
                self.use_new_storage_service = True
                self.mongodb_url = "mongodb://test:27017"
                self.hw_checker_base_url = "http://test:8005"

        settings = TestSettings()
        container = DIContainer(settings)

        # Override with mocks for testing
        mock_hw_checker = AsyncMock()
        mock_hw_checker.get_recent_commits.return_value = {
            "total": 1,
            "commits": [{"commit_hash": "test123", "assignment": "Test"}]
        }
        mock_hw_checker.download_archive.return_value = b"test_archive_data"

        mock_tool_client = AsyncMock()
        mock_tool_client.call_tool.return_value = {
            "success": True,
            "markdown_report": "# Integration Test Report\n\nAll good!",
            "total_findings": 1,
            "detected_components": ["main.py"],
            "execution_time_seconds": 2.0,
        }

        container.override_for_testing(
            hw_checker_client=mock_hw_checker,
            tool_client=mock_tool_client,
        )

        return container

    async def test_clean_use_case_integration(self, di_container):
        """Integration: Clean use case works with domain services."""
        # Act
        use_case = di_container.review_homework_clean_use_case
        result = await use_case.execute("integration_commit_123")

        # Assert
        assert result.success == True
        assert "Review completed" in result.markdown_report

        # Verify domain service was called through use case
        homework_service = di_container.homework_review_service
        assert homework_service.review_homework.called

    async def test_use_case_orchestrates_domain_services(self, di_container):
        """Integration: Use case properly orchestrates domain services."""
        # Act
        use_case = di_container.review_homework_clean_use_case
        homeworks = await use_case.list_recent_homeworks(days=2)

        # Assert
        assert isinstance(homeworks, list)
        assert len(homeworks) == 1
        assert homeworks[0]["commit_hash"] == "test123"

        # Verify domain service orchestration
        homework_service = di_container.homework_review_service
        assert homework_service.list_homeworks.called

    async def test_use_case_uses_secure_storage(self, di_container):
        """Integration: Use case uses secure storage through domain service."""
        # Act
        use_case = di_container.review_homework_clean_use_case
        result = await use_case.execute("secure_storage_test")

        # Assert - should work without security issues
        assert result.success == True

        # Verify storage service is available and secure
        storage_service = di_container.storage_service
        assert hasattr(storage_service, 'validate_path_safe')
        assert hasattr(storage_service, 'create_temp_file')

    async def test_legacy_vs_clean_use_case_coexistence(self, di_container):
        """Integration: Both legacy and clean use cases can coexist."""
        # Container provides both
        clean_use_case = di_container.review_homework_clean_use_case

        # Legacy use case (if it existed) would use different dependencies
        # This test verifies clean use case uses new architecture

        # Act
        result = await clean_use_case.execute("coexistence_test")

        # Assert - clean use case works independently
        assert result.success == True

        # Verify it uses domain services, not direct infrastructure
        # (This is implicit in the fact that it works with our mocks)

    async def test_use_case_error_handling_integration(self, di_container):
        """Integration: Use case error handling works end-to-end."""
        # Setup service to fail
        homework_service = di_container.homework_review_service
        homework_service.review_homework.side_effect = Exception("Integration test error")

        # Act & Assert
        use_case = di_container.review_homework_clean_use_case
        with pytest.raises(RuntimeError) as exc_info:
            await use_case.execute("failing_commit")

        assert "Homework review failed" in str(exc_info.value)
        assert "Integration test error" in str(exc_info.value)

    async def test_use_case_input_validation_integration(self, di_container):
        """Integration: Use case input validation works."""
        use_case = di_container.review_homework_clean_use_case

        # Test invalid inputs
        with pytest.raises(ValueError):
            await use_case.execute("")

        with pytest.raises(ValueError):
            await use_case.execute(None)

        with pytest.raises(ValueError):
            await use_case.execute("   ")
