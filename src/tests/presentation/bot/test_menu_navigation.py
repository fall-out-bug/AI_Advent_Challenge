def test_build_main_menu():
    from src.presentation.bot.handlers.menu import build_main_menu

    keyboard = build_main_menu()
    markup = keyboard.as_markup()
    assert markup.inline_keyboard, "Main menu should contain buttons"


def test_menu_navigation_flow():
    from src.presentation.bot.handlers.menu import build_back_button, build_main_menu

    main_markup = build_main_menu().as_markup()
    buttons = [button.text for row in main_markup.inline_keyboard for button in row]
    assert {"📰 Channels", "📊 Summary", "📮 Digest"}.issubset(set(buttons))

    back_markup = build_back_button().as_markup()
    back_buttons = [
        button.text for row in back_markup.inline_keyboard for button in row
    ]
    assert back_buttons == ["🔙 Back"]
