def test_build_tasks_menu():
    from src.presentation.bot.handlers.tasks import build_tasks_menu

    keyboard = build_tasks_menu()
    assert keyboard is not None


def test_format_task_summary():
    from src.presentation.bot.handlers.tasks import _format_task_summary

    task = {"title": "Buy milk", "priority": "high", "completed": False}
    summary = _format_task_summary(task)
    assert "Buy milk" in summary
    assert "🔴" in summary  # high priority
