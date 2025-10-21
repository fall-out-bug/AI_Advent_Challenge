#!/usr/bin/env python3
"""
Терминальный чат v5: управление температурой, режим «объясняй»,
интерактивные триггеры, режим «дай совет» и поддержка локальных моделей.

Команды:
- temp <value>      — установить дефолтную температуру (пример: temp 0.7)
- объясняй          — включить режим пояснений (показывать температуру и модель)
- надоел            — выключить режим пояснений
- дай совет         — включить режим советчика
- стоп совет        — выключить режим советчика
- модель <name>     — переключить модель (qwen, mistral, tinyllama)
- покеда            — завершить разговор
"""
import asyncio
import sys
import os
import unicodedata
import shutil
import textwrap
import time
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_api_key, is_api_key_configured
from advice_mode_v5 import AdviceModeV5
from temperature_utils import resolve_effective_temperature, clamp_temperature


# Локальные модели
LOCAL_MODELS = {
    "qwen": "http://localhost:8000",
    "mistral": "http://localhost:8001", 
    "tinyllama": "http://localhost:8002"
}

# Внешние API (fallback)
API_URL = "https://api.perplexity.ai/chat/completions"
MODEL = "sonar-pro"
CHAD_URL = 'https://ask.chadgpt.ru/api/public/gpt-5-mini'


def _contains_any(haystack: str, needles: list[str]) -> bool:
    s = haystack.lower()
    return any(n in s for n in needles)


def _normalize_for_trigger(text: str) -> str:
    """
    Purpose: Normalize unicode and punctuation to improve trigger matching.
    """
    if not text:
        return ""
    # Unicode normalize and lower
    norm = unicodedata.normalize('NFKC', text).lower()
    # Replace common separators with space
    for ch in ["\u2013", "\u2014", "-", "_", "|", ",", ".", "!", "?", "\u00A0", "\u2019", "\u2018", "\u201c", "\u201d", "\"", "'", ":", ";", "(", ")", "[", "]", "{" , "}"]:
        norm = norm.replace(ch, " ")
    # Collapse spaces
    norm = " ".join(norm.split())
    return norm


class LocalModelClient:
    """
    Purpose: Client for local model APIs with conversation history support.
    """
    
    def __init__(self, model_url: str):
        self.url = model_url
        self.conversation_history = []
        
    async def chat(self, messages: list, max_tokens: int = 200, temperature: float = 0.7, use_history: bool = False) -> dict:
        """
        Purpose: Send chat request to local model with optional conversation history.
        Args:
            messages: List of message dicts with role and content
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            use_history: Whether to include conversation history
        Returns:
            dict: Response with text and token information
        """
        # Build messages with optional history
        if use_history:
            full_messages = self.conversation_history + messages
        else:
            full_messages = messages
        
        payload = {
            "messages": full_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.post(f"{self.url}/chat", json=payload)
                if response.status_code != 200:
                    return {
                        "response": f"❌ Ошибка локальной модели: {response.status_code}",
                        "input_tokens": 0,
                        "response_tokens": 0,
                        "total_tokens": 0
                    }
                
                data = response.json()
                if "response" not in data:
                    return {
                        "response": "❌ Неожиданный формат ответа от локальной модели",
                        "input_tokens": 0,
                        "response_tokens": 0,
                        "total_tokens": 0
                    }
                
                result = {
                    "response": data["response"].strip(),
                    "input_tokens": data.get("input_tokens", 0),
                    "response_tokens": data.get("response_tokens", 0),
                    "total_tokens": data.get("total_tokens", 0)
                }
                
                # Update conversation history only if using history
                if use_history:
                    self.conversation_history.extend(messages)
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": result["response"]
                    })
                
                return result
        except Exception as e:
            return {
                "response": f"❌ Ошибка подключения к локальной модели: {e}",
                "input_tokens": 0,
                "response_tokens": 0,
                "total_tokens": 0
            }
    
    def clear_history(self):
        """
        Purpose: Clear conversation history.
        """
        self.conversation_history = []
    
    def get_history_length(self) -> int:
        """
        Purpose: Get current conversation history length.
        Returns:
            int: Number of messages in history
        """
        return len(self.conversation_history)


class DedChatV5:
    """
    Purpose: Terminal chat with temperature control, interactive switching, 
    experiment runner and local model support.
    """

    def __init__(self):
        self.api_key = None
        self.client = None
        self.default_temperature = 0.5
        self.explain_mode = False
        self.current_api = None  # "chadgpt", "perplexity", or local model name
        self._system_prompt = "Ты пожилой человек, который ехидно подшучивает. Отвечай на русском, лаконично, без ссылок."
        self.advice_mode: AdviceModeV5 | None = None
        self.local_clients = {name: LocalModelClient(url) for name, url in LOCAL_MODELS.items()}
        self.use_history = False  # Default: no history

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    def setup(self) -> bool:
        """
        Purpose: Ensure at least one API is configured.
        Returns:
            bool: True if configured
        """
        # Check if any local models are available
        if self._check_local_models():
            self.current_api = "mistral"  # Default to mistral
            return True
            
        # Prefer ChadGPT as primary API if configured
        if is_api_key_configured("chadgpt"):
            self.current_api = "chadgpt"
            self.api_key = get_api_key("chadgpt")
            return True
        # Fallback to Perplexity
        if is_api_key_configured("perplexity"):
            self.current_api = "perplexity"
            self.api_key = get_api_key("perplexity")
            return True
            
        print("❌ Ни один API ключ не настроен и локальные модели недоступны!")
        print("   Установите CHAD_API_KEY или PERPLEXITY_API_KEY, или запустите локальные модели")
        return False

    def _check_local_models(self) -> bool:
        """
        Purpose: Check if any local models are available.
        Returns:
            bool: True if at least one local model is available
        """
        # For now, assume local models are available if docker-compose is running
        # In production, you might want to ping each endpoint
        return True

    def print_welcome(self) -> None:
        """
        Purpose: Print welcome and help.
        """
        print("👴" + "=" * 60)
        print("👴  ДЕДУШКА AI v5 — Температура, Поясняй, Советчик и Локальные Модели")
        print("👴" + "=" * 60)
        print("👣 Как общаться:")
        print("  • Просто задавайте вопросы. Я отвечу ехидно и по делу.")
        print("  • Температура влияет на креативность: ниже — точнее, выше — смелее.")
        print()
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
        print("📦 Триггеры авто‑температуры (по тексту ответа):")
        print("  • 'не душни' → T=0.0   • 'потише' → T=0.7   • 'разгоняй' → T=1.2")
        print()
        print("🤖 Доступные модели:")
        for name, url in LOCAL_MODELS.items():
            status = "🟢" if self.current_api == name else "⚪"
            print(f"  {status} {name} — {url}")
        print()

    async def call_perplexity(self, message: str, temperature: float, system_prompt: str | None = None) -> str:
        """
        Purpose: Call Perplexity chat completion with given temperature.
        Args:
            message: User prompt
            temperature: Effective temperature
        Returns:
            str: Model reply
        """
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": (system_prompt or self._system_prompt)},
                {"role": "user", "content": message}
            ],
            "max_tokens": 800,
            "temperature": temperature
        }
        try:
            r = await self.client.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            if r.status_code != 200:
                body = r.text
                preview = body[:240].replace("\n", " ") if body else ""
                return f"❌ Ошибка API Perplexity: {r.status_code} {preview}"
            data = r.json()
            if "choices" not in data or not data["choices"]:
                return "❌ Неожиданный формат ответа от API Perplexity"
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"❌ Ошибка Perplexity: {e}"

    async def call_chadgpt(self, message: str, temperature: float, system_prompt: str | None = None) -> str:
        """
        Purpose: Call ChadGPT API. Temperature is not supported by API; retained for display.
        Args:
            message: User message
            temperature: Effective temperature (display only)
        Returns:
            str: Model reply
        """
        prompt_text = f"{(system_prompt or self._system_prompt)}\n\nВопрос: {message}"
        request_json = {
            "message": prompt_text,
            "api_key": self.api_key,
            "temperature": float(f"{temperature:.2f}"),
            "max_tokens": 800
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(CHAD_URL, json=request_json)
                if resp.status_code != 200:
                    return f"❌ Ошибка API: {resp.status_code}"
                data = resp.json()
                if data.get('is_success') and isinstance(data.get('response'), str):
                    return data['response'].strip()
                return "❌ Неожиданный формат ответа от API"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    async def call_local_model(self, message: str, temperature: float, system_prompt: str | None = None, use_history: bool = False) -> dict:
        """
        Purpose: Call local model API.
        Args:
            message: User message
            temperature: Effective temperature
            system_prompt: System prompt override
            use_history: Whether to use conversation history
        Returns:
            dict: Response with text and token information
        """
        if self.current_api not in self.local_clients:
            return {
                "response": f"❌ Неизвестная локальная модель: {self.current_api}",
                "input_tokens": 0,
                "response_tokens": 0,
                "total_tokens": 0
            }
            
        messages = [
            {"role": "system", "content": (system_prompt or self._system_prompt)},
            {"role": "user", "content": message}
        ]
        
        return await self.local_clients[self.current_api].chat(
            messages=messages,
            max_tokens=800,
            temperature=temperature,
            use_history=use_history
        )

    async def call_model(self, message: str, temperature: float, system_prompt: str | None = None, use_history: bool = False) -> dict:
        """
        Purpose: Route call to current API (chadgpt/perplexity/local).
        Returns:
            dict: Response with text and optional token information
        """
        if self.current_api in self.local_clients:
            return await self.call_local_model(message, temperature, system_prompt, use_history)
        elif self.current_api == "chadgpt":
            response_text = await self.call_chadgpt(message, temperature, system_prompt)
            return {
                "response": response_text,
                "input_tokens": 0,
                "response_tokens": 0,
                "total_tokens": 0
            }
        else:
            response_text = await self.call_perplexity(message, temperature, system_prompt)
            return {
                "response": response_text,
                "input_tokens": 0,
                "response_tokens": 0,
                "total_tokens": 0
            }

    def parse_temp_override(self, user_message: str):
        """
        Purpose: Parse one-off override in 'temp=<v> <text>'.
        Args:
            user_message: Raw input
        Returns:
            (override: float|None, clean_text: str)
        """
        msg = user_message.strip()
        if not msg.lower().startswith("temp="):
            return None, msg
        try:
            head, rest = msg.split(maxsplit=1)
        except ValueError:
            head, rest = msg, ""
        try:
            override = float(head.split("=", 1)[1])
            override = clamp_temperature(override)
        except Exception as e:
            print(f"❌ Неверный формат temp=<value>: {e}")
            return None, rest.strip()
        return override, rest.strip()

    def apply_interactive_temperature(self, reply_text: str) -> None:
        """
        Purpose: Adjust default_temperature based on reply content.
        Rules:
            - contains "не душни" -> 0.0
            - contains "разгоняй" -> 1.2
            - contains "потише"   -> 0.7
        """
        txt = _normalize_for_trigger(reply_text)
        if "не душни" in txt:
            self.default_temperature = clamp_temperature(0.0)
            print("🔧 Автопереключение: темп. = 0.0 (по фразе 'не душни')\n")
        elif "разгоняй" in txt:
            self.default_temperature = clamp_temperature(1.2)
            print("🔧 Автопереключение: темп. = 1.2 (по фразе 'разгоняй')\n")
        elif "потише" in txt:
            self.default_temperature = clamp_temperature(0.7)
            print("🔧 Автопереключение: темп. = 0.7 (по фразе 'потише')\n")

    def print_ded_message(self, message: str, eff_temp: float | None = None) -> None:
        """
        Purpose: Pretty-print model message with optional T-indicator.
        In explain_mode, temperature is always shown.
        Args:
            message: Text to print
            eff_temp: Effective temperature indicator
        """
        width = shutil.get_terminal_size((100, 20)).columns
        prefix = "👴 Дедушка"
        model_label = self.get_model_label()
        if self.explain_mode:
            t = eff_temp if eff_temp is not None else self.default_temperature
            prefix = f"{prefix} [T={t:.2f} • {model_label}]"
        suffix = ""
        if not self.explain_mode:
            suffix = ""
        wrapped = textwrap.fill(f"{prefix}: {message}{suffix}", width=width)
        print(wrapped)
        print()

    def get_model_label(self) -> str:
        """
        Purpose: Human-readable model label for indicators.
        """
        if self.current_api in self.local_clients:
            return f"local:{self.current_api}"
        elif self.current_api == "chadgpt":
            return "chadgpt:gpt-5-mini"
        return f"perplexity:{MODEL}"

    def get_api_endpoint(self) -> str:
        """
        Purpose: Return API endpoint URL for current provider.
        """
        if self.current_api in self.local_clients:
            return LOCAL_MODELS[self.current_api]
        return CHAD_URL if self.current_api == "chadgpt" else API_URL

    def print_debug_info(self, user_message: str, reply_data: dict, eff_temp: float, sys_prompt: str | None, duration_ms: int) -> None:
        """
        Purpose: Print extended debug info in explain mode.
        """
        if not self.explain_mode:
            return
        width = shutil.get_terminal_size((100, 20)).columns
        model_label = self.get_model_label()
        endpoint = self.get_api_endpoint()
        mode = "advice" if sys_prompt else "normal"
        prompt_preview = (sys_prompt or self._system_prompt)[:120].replace("\n", " ")
        
        reply_text = reply_data.get("response", "")
        input_tokens = reply_data.get("input_tokens", 0)
        response_tokens = reply_data.get("response_tokens", 0)
        total_tokens = reply_data.get("total_tokens", 0)
        
        lines = [
            "🔍 Debug:",
            f"  api: {self.current_api}",
            f"  endpoint: {endpoint}",
            f"  model: {model_label}",
            f"  temperature: {eff_temp:.2f}",
            f"  mode: {mode}",
            f"  prompt(sys)≈: {prompt_preview}",
            f"  req_len: {len(user_message)} chars",
            f"  resp_len: {len(reply_text)} chars",
            f"  time: {duration_ms} ms ({duration_ms/1000:.2f}s)",
        ]
        
        # Add token information for local models
        if self.current_api in self.local_clients and total_tokens > 0:
            lines.extend([
                f"  input_tokens: {input_tokens}",
                f"  response_tokens: {response_tokens}",
                f"  total_tokens: {total_tokens}"
            ])
        
        print(textwrap.fill("\n".join(lines), width=width))
        print()

    def get_user_input(self) -> str:
        """
        Purpose: Read user input with temperature indicator.
        Returns:
            str: Raw input
        """
        try:
            t = f"{self.default_temperature:.2f}"
            mode = " [ПОЯСНЯЙ]" if self.explain_mode else ""
            model_label = self.get_model_label()
            return input(f"🤔 Вы{mode} [T={t} • {model_label}]: ").strip()
        except KeyboardInterrupt:
            print("\n👴 Дедушка: До свидания!")
            sys.exit(0)
        except EOFError:
            print("\n👴 Дедушка: До свидания!")
            sys.exit(0)

    async def run(self):
        """
        Purpose: Main loop.
        """
        if not self.setup():
            return
        self.print_welcome()
        # init advice mode helper (idle by default)
        self.advice_mode = AdviceModeV5(self.api_key, self.current_api)
        welcome_data = await self.call_model("Привет! Дай короткое ехидное приветствие.", self.default_temperature, use_history=self.use_history)
        self.print_ded_message(welcome_data["response"], self.default_temperature)
        self.apply_interactive_temperature(welcome_data["response"])

        while True:
            user_message = self.get_user_input()
            if not user_message:
                continue

            low = user_message.lower()

            # exit by substring (only "покеда")
            if _contains_any(low, ["покеда"]):
                bye_data = await self.call_model("Скажи короткое ехидное прощание.", self.default_temperature, use_history=self.use_history)
                self.print_ded_message(bye_data["response"], self.default_temperature)
                self.apply_interactive_temperature(bye_data["response"])
                break

            # API switching: 'api chadgpt', 'api perplexity', 'api local-qwen', etc.
            if low.startswith("api "):
                new_api = low.split()[1]
                
                # Handle local models with 'local-' prefix
                if new_api.startswith("local-"):
                    local_model = new_api[6:]  # Remove 'local-' prefix
                    if local_model in LOCAL_MODELS:
                        self.current_api = local_model
                        # Re-init advice mode helper with new API
                        self.advice_mode = AdviceModeV5(self.api_key, self.current_api)
                        print(f"👴 Дедушка: Переключаюсь на локальную модель {local_model}!")
                        print()
                    else:
                        print(f"❌ Неизвестная локальная модель '{local_model}'. Доступные: {', '.join(LOCAL_MODELS.keys())}")
                        print()
                # Handle external APIs
                elif new_api in ("chadgpt", "perplexity"):
                    if not is_api_key_configured(new_api):
                        print(f"❌ API '{new_api}' не настроен. Проверьте ключ.")
                        print()
                    else:
                        self.current_api = new_api
                        self.api_key = get_api_key(new_api)
                        # Re-init advice mode helper with new API
                        self.advice_mode = AdviceModeV5(self.api_key, self.current_api)
                        print(f"👴 Дедушка: Переключаюсь на {new_api}!")
                        print()
                else:
                    available_apis = ["chadgpt", "perplexity"] + [f"local-{name}" for name in LOCAL_MODELS.keys()]
                    print(f"❌ Неизвестный API '{new_api}'. Доступные: {', '.join(available_apis)}")
                    print()
                continue

            # explain mode on/off by substring
            if "объясняй" in low:
                self.explain_mode = True
                print("👴 Дедушка: Включил режим пояснений (температура будет показываться).")
                print()
                continue

            if "надоел" in low:
                # Only turns off explain mode (not advice)
                self.explain_mode = False
                print("👴 Дедушка: Выключил режим пояснений.")
                print()
                # do not continue; allow message to be processed below

            # history toggle command
            if "история вкл" in low:
                self.use_history = True
                print("👴 Дедушка: История сообщений включена!")
                print()
                continue
            
            if "история выкл" in low:
                self.use_history = False
                print("👴 Дедушка: История сообщений выключена!")
                print()
                continue

            # clear history command
            if "очисти историю" in low:
                if self.current_api in self.local_clients:
                    self.local_clients[self.current_api].clear_history()
                    print("👴 Дедушка: История сообщений очищена!")
                else:
                    print("👴 Дедушка: Очистка истории доступна только для локальных моделей.")
                print()
                continue

            # help by substring
            if "помогай" in low:
                print("🔧 Команды:")
                print("  • temp <value>         — установить температуру по умолчанию (0.0–1.5)")
                print("  • объясняй             — включить режим пояснений (показывать T и модель)")
                print("  • надоел               — выключить режим пояснений")
                print("  • история вкл/выкл     — включить/выключить историю сообщений")
                print("  • очисти историю       — очистить историю сообщений (для локальных моделей)")
                print("  • покеда               — завершить разговор")
                print("  • api <provider>       — переключить API (chadgpt, perplexity, local-qwen, local-mistral, local-tinyllama)")
                print()
                print("📦 Триггеры авто‑температуры (по тексту): 'не душни' → 0.0, 'потише' → 0.7, 'разгоняй' → 1.2")
                print()
                continue

            if low.startswith("temp "):
                try:
                    value = float(user_message.split()[1])
                    self.default_temperature = clamp_temperature(value)
                    print(f"👴 Дедушка: Температура по умолчанию {self.default_temperature}")
                except Exception as e:
                    print(f"❌ {e}")
                print()
                continue

            # Apply temperature triggers from USER message as well
            self.apply_interactive_temperature(user_message)
            # If user message contained any control words, do not forward it to API
            if any(k in low for k in ["объясняй", "надоел", "помогай"]) or low.startswith("temp "):
                continue

            # Advice mode triggers and routing (from day_03 behavior)
            if "дай совет" in low:
                print("👴 Дедушка: Включаю режим советчика...")
                print()
                # Prime advice mode with the user message
                print("👴 Дедушка печатает...", end="", flush=True)
                reply = await self.advice_mode.handle_advice_request(user_message)
                print("\r" + " " * 30 + "\r", end="")
                self.print_ded_message(rely := reply, self.default_temperature)
                self.apply_interactive_temperature(rely)
                continue

            if self.advice_mode and self.advice_mode.is_advice_mode_active():
                print("👴 Дедушка печатает...", end="", flush=True)
                reply = await self.advice_mode.handle_advice_request(user_message)
                print("\r" + " " * 30 + "\r", end="")
                self.print_ded_message(rely2 := reply, self.default_temperature)
                self.apply_interactive_temperature(rely2)
                # If advice session ended internally after final advice, continue to next turn
                if not self.advice_mode.is_advice_mode_active():
                    print()
                continue

            # per-message temp override removed; always use default_temperature
            eff = self.default_temperature
            print("👴 Дедушка печатает...", end="", flush=True)
            start_ts = time.time()
            reply_data = await self.call_model(user_message, eff, use_history=self.use_history)
            duration_ms = int((time.time() - start_ts) * 1000)
            print("\r" + " " * 30 + "\r", end="")
            self.print_ded_message(reply_data["response"], eff)
            # Debug info (explain mode only)
            self.print_debug_info(user_message, reply_data, eff, None, duration_ms)
            self.apply_interactive_temperature(reply_data["response"])


async def main():
    chat = DedChatV5()
    async with chat:
        await chat.run()


if __name__ == "__main__":
    asyncio.run(main())
