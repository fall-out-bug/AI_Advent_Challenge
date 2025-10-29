import pytest


def test_build_main_menu():
    from src.presentation.bot.handlers.menu import build_main_menu

    keyboard = build_main_menu()
    assert keyboard is not None


def test_menu_navigation_flow():
    from src.presentation.bot.handlers.menu import build_main_menu
    from src.presentation.bot.handlers.tasks import build_tasks_menu

    main = build_main_menu()
    tasks = build_tasks_menu()
    assert main is not None
    assert tasks is not None

