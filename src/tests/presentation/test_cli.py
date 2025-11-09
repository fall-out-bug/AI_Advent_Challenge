"""Tests for presentation CLI layer."""

from unittest.mock import patch

from src.presentation.cli.main_cli import handle_status, print_usage


def test_print_usage(capsys) -> None:
    """Test usage printing."""
    print_usage()
    captured = capsys.readouterr()
    assert "Usage:" in captured.out
    assert "generate" in captured.out
    assert "status" in captured.out
    assert "metrics" in captured.out


def test_handle_status(capsys) -> None:
    """Test status handling."""
    with patch(
        "src.presentation.cli.commands.status_cmd.display_status"
    ) as mock_display:
        handle_status()
        mock_display.assert_called_once()


def test_handle_health(capsys) -> None:
    """Test health handling."""
    with patch("src.presentation.cli.commands.health_cmd.check_health") as mock_check:
        mock_check.return_value = 0
        with patch("sys.exit") as mock_exit:
            from src.presentation.cli.main_cli import handle_health

            handle_health()
            mock_check.assert_called_once()
            mock_exit.assert_called_once()


def test_cli_imports() -> None:
    """Test that CLI modules import correctly."""
    from src.presentation.cli import main_cli

    assert hasattr(main_cli, "handle_generate")
    assert hasattr(main_cli, "handle_review")
    assert hasattr(main_cli, "handle_health")
    assert hasattr(main_cli, "handle_status")
