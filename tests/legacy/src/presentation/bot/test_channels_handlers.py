def test_build_channels_menu():
    from src.presentation.bot.handlers.channels import build_channels_menu

    keyboard = build_channels_menu()
    assert keyboard is not None
