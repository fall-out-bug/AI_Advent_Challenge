"""
Terminal UI for chat application.

Following Python Zen: "Simple is better than complex"
and "Readability counts".
"""

import sys
import shutil
import textwrap
from typing import Optional, Dict, Any

# Mock LOCAL_MODELS for testing
try:
    from shared_package.config.models import LOCAL_MODELS
except ImportError:
    LOCAL_MODELS = {
        "qwen": "http://localhost:8000",
        "mistral": "http://localhost:8001", 
        "tinyllama": "http://localhost:8002"
    }


class TerminalUI:
    """Handles all terminal UI operations for chat application."""
    
    def __init__(self, chat_state):
        """Initialize UI with chat state reference."""
        self.state = chat_state
    
    def print_welcome(self) -> None:
        """Print welcome message and help."""
        print("👴" + "=" * 60)
        print("👴  ДЕДУШКА AI v5 — Температура, Поясняй, Советчик и Локальные Модели")
        print("👴" + "=" * 60)
        print("👣 Как общаться:")
        print("  • Просто задавайте вопросы. Я отвечу ехидно и по делу.")
        print("  • Температура влияет на креативность: ниже — точнее, выше — смелее.")
        print()
        self._print_commands()
        self._print_triggers()
        self._print_models()
        print()
    
    def _print_commands(self) -> None:
        """Print available commands."""
        print("🔧 Команды:")
        print("  • temp <value>         — установить температуру по умолчанию (0.0–1.5)")
        print("  • объясняй             — включить режим пояснений (показывать T и модель)")
        print("  • надоел               — выключить пояснения и/или советчика")
        print("  • дай совет            — включить режим советчика")
        print("  • история вкл/выкл     — включить/выключить историю сообщений")
        print("  • очисти историю       — очистить историю сообщений (для локальных моделей)")
        print("  • покеда               — завершить разговор")
        print("  • api <provider>       — переключить API (chadgpt, perplexity, local-qwen, local-mistral, local-tinyllama)")
        print()
    
    def _print_triggers(self) -> None:
        """Print temperature triggers."""
        print("📦 Триггеры авто‑температуры (по тексту ответа):")
        print("  • 'не душни' → T=0.0   • 'потише' → T=0.7   • 'разгоняй' → T=1.2")
        print()
    
    def _print_models(self) -> None:
        """Print available models."""
        print("🤖 Доступные модели:")
        for name, url in LOCAL_MODELS.items():
            status = "🟢" if self.state.current_api == name else "⚪"
            print(f"  {status} {name} — {url}")
    
    def print_ded_message(self, message: str, eff_temp: Optional[float] = None) -> None:
        """
        Pretty-print model message with optional temperature indicator.
        
        Args:
            message: The response message from the AI model
            eff_temp: Effective temperature used for generation (optional)
            
        Note:
            Temperature indicator is only shown when explain_mode is enabled
        """
        width = shutil.get_terminal_size((100, 20)).columns
        prefix = "👴 Дедушка"
        
        if self.state.explain_mode:
            t = eff_temp if eff_temp is not None else self.state.default_temperature
            model_label = self._get_model_label()
            prefix = f"{prefix} [T={t:.2f} • {model_label}]"
        
        wrapped = textwrap.fill(f"{prefix}: {message}", width=width)
        print(wrapped)
        print()
    
    def _get_model_label(self) -> str:
        """Get human-readable model label."""
        if self.state.current_api in self.state.local_clients:
            return f"local:{self.state.current_api}"
        elif self.state.current_api == "chadgpt":
            return "chadgpt:gpt-5-mini"
        return f"perplexity:sonar-pro"
    
    def print_debug_info(
        self, 
        user_message: str, 
        reply_data: Dict[str, Any], 
        eff_temp: float, 
        sys_prompt: Optional[str], 
        duration_ms: int
    ) -> None:
        """Print extended debug info in explain mode."""
        if not self.state.explain_mode:
            return
            
        width = shutil.get_terminal_size((100, 20)).columns
        model_label = self._get_model_label()
        endpoint = self._get_api_endpoint()
        mode = "advice" if sys_prompt else "normal"
        prompt_preview = (sys_prompt or self.state.get_system_prompt())[:120].replace("\n", " ")
        
        debug_lines = [
            f"🔍 DEBUG [{mode}]",
            f"  Model: {model_label}",
            f"  Endpoint: {endpoint}",
            f"  Temperature: {eff_temp:.3f}",
            f"  Duration: {duration_ms}ms",
            f"  Tokens: {reply_data.get('total_tokens', 0)}",
            f"  Prompt: {prompt_preview}...",
            f"  User: {user_message[:80]}..."
        ]
        
        for line in debug_lines:
            print(textwrap.fill(line, width=width))
        print()
    
    def _get_api_endpoint(self) -> str:
        """Get API endpoint URL for current provider."""
        if self.state.current_api in self.state.local_clients:
            from shared_package.config.models import LOCAL_MODELS
            return LOCAL_MODELS[self.state.current_api]
        elif self.state.current_api == "chadgpt":
            return "https://ask.chadgpt.ru/api/public/gpt-5-mini"
        return "https://api.perplexity.ai/chat/completions"
    
    def get_user_input(self) -> str:
        """Read user input with temperature indicator."""
        try:
            t = f"{self.state.default_temperature:.2f}"
            mode = " [ПОЯСНЯЙ]" if self.state.explain_mode else ""
            model_label = self._get_model_label()
            return input(f"🤔 Вы{mode} [T={t} • {model_label}]: ").strip()
        except KeyboardInterrupt:
            print("\n👴 Дедушка: До свидания!")
            sys.exit(0)
        except EOFError:
            print("\n👴 Дедушка: До свидания!")
            sys.exit(0)
    
    def print_error(self, message: str) -> None:
        """Print error message."""
        print(f"❌ {message}")
    
    def print_success(self, message: str) -> None:
        """Print success message."""
        print(f"✅ {message}")
    
    def print_info(self, message: str) -> None:
        """Print info message."""
        print(f"ℹ️  {message}")
