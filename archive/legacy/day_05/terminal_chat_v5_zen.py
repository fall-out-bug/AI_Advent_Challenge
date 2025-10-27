#!/usr/bin/env python3
"""
Терминальный чат v5 (Zen-версия): идеальная модульная архитектура.

Следует всем принципам Дзена Python:
- "Simple is better than complex"
- "Explicit is better than implicit" 
- "Flat is better than nested"
- "Beautiful is better than ugly"
- "Readability counts"
"""

import asyncio
import sys
import time
from typing import Optional

from utils.text_utils import resolve_effective_temperature

# Import modular components
from state.chat_state import ChatState
from ui.terminal_ui import TerminalUI
from business.chat_logic import ChatLogic
from business.advice_mode import AdviceModeV5
from utils.text_utils import contains_any, normalize_for_trigger


class DedChatV5Zen:
    """
    Terminal chat with perfect Zen architecture.
    
    Following Python Zen: "Simple is better than complex"
    and "Explicit is better than implicit".
    """
    
    def __init__(self):
        """Initialize chat application with dependency injection."""
        self.state = ChatState()
        self.ui = TerminalUI(self.state)
        self.logic = ChatLogic(self.state)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.state.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.state.__aexit__(exc_type, exc_val, exc_tb)
    
    def setup(self) -> bool:
        """Setup chat application."""
        return self.state.setup()
    
    async def run(self):
        """Main chat loop - simple and clean."""
        self.ui.print_welcome()
        
        while True:
            user_input = self.ui.get_user_input()
            
            if await self._handle_command(user_input):
                continue
            
            await self._process_message(user_input)
    
    async def _handle_command(self, user_input: str) -> bool:
        """
        Handle user commands.
        
        Returns True if command was handled, False if it's a regular message.
        """
        cmd = user_input.lower().strip()
        
        # Simple command dispatch - flat structure
        if cmd == "покеда":
            return self._handle_exit()
        elif cmd == "объясняй":
            return self._handle_explain_mode(True)
        elif cmd == "надоел":
            return self._handle_explain_mode(False)
        elif cmd == "дай совет":
            return self._handle_advice_mode(True)
        elif cmd.startswith("temp "):
            return self._handle_temp_command(cmd)
        elif cmd.startswith("api "):
            return self._handle_api_command(cmd)
        elif cmd in ["история вкл", "история выкл"]:
            return self._handle_history_command(cmd)
        elif cmd == "очисти историю":
            return self._handle_clear_history_command()
        
        return False
    
    def _handle_exit(self) -> bool:
        """Handle exit command."""
        print("👴 Дедушка: До свидания!")
        sys.exit(0)
    
    def _handle_explain_mode(self, enabled: bool) -> bool:
        """Handle explain mode toggle."""
        self.state.set_explain_mode(enabled)
        if not enabled and self.state.advice_mode:
            self.state.advice_mode = None
        
        status = "включен" if enabled else "выключен"
        self.ui.print_success(f"Режим пояснений {status}")
        return True
    
    def _handle_advice_mode(self, enabled: bool) -> bool:
        """Handle advice mode toggle."""
        if enabled:
            self.state.advice_mode = AdviceModeV5()
            self.ui.print_success("Режим советчика включен")
        return True
    
    def _handle_temp_command(self, cmd: str) -> bool:
        """Handle temperature command."""
        try:
            temp_str = cmd.split()[1]
            temp = float(temp_str)
            temp = max(0.0, min(1.5, temp))  # Clamp to valid range
            self.state.set_temperature(temp)
            self.ui.print_success(f"Температура установлена: {temp:.2f}")
            return True
        except (IndexError, ValueError):
            self.ui.print_error("Неверный формат: temp <value>")
            return True
    
    def _handle_api_command(self, cmd: str) -> bool:
        """Handle API switching command."""
        try:
            api_name = cmd.split()[1]
            if self.logic.switch_model(api_name):
                self.ui.print_success(f"Переключено на: {api_name}")
            else:
                self.ui.print_error(f"Неизвестный API: {api_name}")
            return True
        except IndexError:
            self.ui.print_error("Неверный формат: api <provider>")
            return True
    
    def _handle_history_command(self, cmd: str) -> bool:
        """Handle history command."""
        enabled = cmd == "история вкл"
        self.state.set_history_usage(enabled)
        status = "включена" if enabled else "выключена"
        self.ui.print_success(f"История сообщений {status}")
        return True
    
    def _handle_clear_history_command(self) -> bool:
        """Handle clear history command."""
        if self.state.current_api in self.state.local_clients:
            client = self.state.local_clients[self.state.current_api]
            client.clear_history()
            self.ui.print_success("История сообщений очищена")
        else:
            self.ui.print_error("История доступна только для локальных моделей")
        return True
    
    async def _process_message(self, user_input: str):
        """Process user message - clean and simple."""
        # Parse temperature override
        temp_override, clean_message = self.logic.parse_temp_override(user_input)
        
        # Determine effective temperature
        eff_temp = resolve_effective_temperature(
            temp_override, self.state.default_temperature
        )
        
        # Get system prompt
        sys_prompt = None
        if self.state.advice_mode:
            sys_prompt = self.state.advice_mode.get_system_prompt()
        
        # Call model
        start_time = time.time()
        reply_data = await self.logic.call_model(
            clean_message, eff_temp, sys_prompt, self.state.use_history
        )
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Apply interactive temperature
        self.logic.apply_interactive_temperature(reply_data["response"])
        
        # Print response
        self.ui.print_ded_message(reply_data["response"], eff_temp)
        
        # Print debug info if needed
        self.ui.print_debug_info(
            clean_message, reply_data, eff_temp, sys_prompt, duration_ms
        )


async def main():
    """
    Main entry point.
    
    Following Python Zen: "Simple is better than complex"
    and proper resource management.
    """
    async with DedChatV5Zen() as chat:
        if not chat.setup():
            return
        await chat.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👴 Дедушка: До свидания!")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
