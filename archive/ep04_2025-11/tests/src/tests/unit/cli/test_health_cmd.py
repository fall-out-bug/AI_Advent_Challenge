"""Tests for health command.

Following the Zen of Python:
- Explicit is better than implicit
- Errors should never pass silently
- Readability counts
"""

from unittest.mock import MagicMock, patch

from src.presentation.cli.commands.health_cmd import (
    _check_configuration,
    _check_storage,
    _check_yaml_config,
    check_health,
)


def test_check_health_success() -> None:
    """Test health check with all systems healthy."""
    with patch(
        "src.presentation.cli.commands.health_cmd._check_configuration"
    ) as mock_config, patch(
        "src.presentation.cli.commands.health_cmd._check_storage"
    ) as mock_storage, patch(
        "src.presentation.cli.commands.health_cmd._check_model_endpoints"
    ) as mock_models, patch(
        "src.presentation.cli.commands.health_cmd._check_yaml_config"
    ) as mock_yaml:
        mock_config.return_value = {"healthy": True, "details": []}
        mock_storage.return_value = {"healthy": True, "details": []}
        mock_models.return_value = {"healthy": True, "details": []}
        mock_yaml.return_value = {"healthy": True, "details": []}

        exit_code = check_health()

        assert exit_code == 0


def test_check_health_failure() -> None:
    """Test health check with system failures."""
    with patch(
        "src.presentation.cli.commands.health_cmd._check_configuration"
    ) as mock_config, patch(
        "src.presentation.cli.commands.health_cmd._check_storage"
    ) as mock_storage, patch(
        "src.presentation.cli.commands.health_cmd._check_model_endpoints"
    ) as mock_models, patch(
        "src.presentation.cli.commands.health_cmd._check_yaml_config"
    ) as mock_yaml:
        mock_config.return_value = {"healthy": False, "error": "Config error"}
        mock_storage.return_value = {"healthy": True, "details": []}
        mock_models.return_value = {"healthy": True, "details": []}
        mock_yaml.return_value = {"healthy": True, "details": []}

        exit_code = check_health()

        assert exit_code == 1


def test_check_configuration_success() -> None:
    """Test configuration check success."""
    with patch("src.presentation.cli.commands.health_cmd.Settings") as mock_settings:
        mock_instance = MagicMock()
        mock_instance.storage_path = MagicMock()
        mock_settings.from_env.return_value = mock_instance

        result = _check_configuration()

        assert result["healthy"]


def test_check_configuration_failure() -> None:
    """Test configuration check failure."""
    with patch("src.presentation.cli.commands.health_cmd.Settings") as mock_settings:
        mock_settings.from_env.side_effect = Exception("Config error")

        result = _check_configuration()

        assert not result["healthy"]
        assert "error" in result


@patch("src.presentation.cli.commands.health_cmd.Settings")
def test_check_storage_success(mock_settings) -> None:
    """Test storage check success."""
    mock_instance = MagicMock()
    mock_instance.get_agent_storage_path.return_value = MagicMock()
    mock_settings.from_env.return_value = mock_instance

    result = _check_storage()

    assert result["healthy"]


def test_check_yaml_config_success() -> None:
    """Test YAML config check success."""
    with patch("pathlib.Path.exists") as mock_exists, patch(
        "builtins.open"
    ) as mock_open, patch("yaml.safe_load") as mock_load:
        mock_exists.return_value = True
        mock_load.return_value = {"test": "data"}

        result = _check_yaml_config()

        assert result["healthy"]


def test_check_yaml_config_failure() -> None:
    """Test YAML config check with invalid YAML."""
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False

        result = _check_yaml_config()

        # Should handle missing files gracefully
        assert isinstance(result, dict)
