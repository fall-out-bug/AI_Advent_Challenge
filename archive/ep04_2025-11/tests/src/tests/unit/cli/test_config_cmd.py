"""Tests for config command.

Following TDD principles and Zen of Python.
"""

from unittest.mock import patch

from src.presentation.cli.commands.config_cmd import (
    display_configuration,
    list_experiments,
    validate_configuration,
)


def test_display_configuration(capsys) -> None:
    """Test configuration display."""
    display_configuration()

    captured = capsys.readouterr()
    assert "Application Configuration" in captured.out
    assert "Settings" in captured.out


def test_validate_configuration_success(capsys) -> None:
    """Test configuration validation with valid configs."""
    with patch("pathlib.Path.exists") as mock_exists, patch(
        "builtins.open"
    ) as mock_open, patch("yaml.safe_load") as mock_load:
        mock_exists.return_value = True
        mock_load.return_value = {"test": "data"}

        result = validate_configuration()

        assert result
        captured = capsys.readouterr()
        assert "valid" in captured.out


def test_validate_configuration_missing_files(capsys) -> None:
    """Test configuration validation with missing files."""
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False

        result = validate_configuration()

        assert not result


@patch("pathlib.Path.exists")
def test_list_experiments_none(mock_exists) -> None:
    """Test listing experiments when none exist."""
    mock_exists.return_value = False

    # Should not crash
    list_experiments()


@patch("pathlib.Path.glob")
def test_list_experiments_with_data(mock_glob, capsys) -> None:
    """Test listing experiments with available templates."""
    from pathlib import Path

    # Use real Path objects instead of mocks
    mock_template1 = Path("config/experiment_templates/test_template.yaml")
    mock_template2 = Path("config/experiment_templates/another_template.yaml")

    mock_glob.return_value = [mock_template1, mock_template2]

    list_experiments()

    captured = capsys.readouterr()
    assert "test_template" in captured.out or "another_template" in captured.out
