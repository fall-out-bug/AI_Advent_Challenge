#!/usr/bin/env python3
"""
Терминальный чат v4: управление температурой, режим «объясняй»,
интерактивные триггеры и режим «дай совет».

Команды:
- temp <value>      — установить дефолтную температуру (пример: temp 0.7)
- объясняй          — включить режим пояснений (показывать температуру и модель)
- надоел            — выключить режим пояснений
- дай совет         — включить режим советчика
- стоп совет        — выключить режим советчика
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
from day_04.advice_mode import AdviceMode
from day_04.temperature_utils import resolve_effective_temperature, clamp_temperature


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


class DedChatV4:
	"""
	Purpose: Terminal chat with temperature control, interactive switching and experiment runner.
	"""

	def __init__(self):
		self.api_key = None
		self.client = None
		self.default_temperature = 0.7
		self.explain_mode = False
		self.current_api = None  # "chadgpt" or "perplexity"
		self._system_prompt = "Ты пожилой человек, который ехидно подшучивает. Отвечай на русском, лаконично, без ссылок."
		self.advice_mode: AdviceMode | None = None

	async def __aenter__(self):
		self.client = httpx.AsyncClient(timeout=30.0)
		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		if self.client:
			await self.client.aclose()

	def setup(self) -> bool:
		"""
		Purpose: Ensure Perplexity API key is configured.
		Returns:
			bool: True if configured
		"""
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
		print("❌ Ни один API ключ не настроен! Установите CHAD_API_KEY или PERPLEXITY_API_KEY")
		return False

	def print_welcome(self) -> None:
		"""
		Purpose: Print welcome and help.
		"""
		print("👴" + "=" * 60)
		print("👴  ДЕДУШКА AI v4 — Температура, Поясняй и Советчик")
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
		print("  • покеда               — завершить разговор")
		print("  • api chadgpt|perplexity — переключить провайдера API")
		print()
		print("📦 Триггеры авто‑температуры (по тексту ответа):")
		print("  • ‘не душни’ → T=0.0   • ‘потише’ → T=0.7   • ‘разгоняй’ → T=1.2")
		print()

	async def call_perplexity(self, message: str, temperature: float, system_prompt: str | None = None) -> str:
		"""
		Purpose: Call Perplexity chat completion with given temperature.
		Args:
			message: User prompt
			temperature: Effective temperature
		Returns:
			str: Model reply
		Exceptions:
			Returns error string on non-200 or malformed response
		Example:
			await call_perplexity("Привет", 0.7)
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
				# include snippet of error body for diagnostics
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
		# Pass a composed prompt without history in normal conversation
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
				# Expected format from day_03 code: {'is_success': bool, 'response': str}
				if data.get('is_success') and isinstance(data.get('response'), str):
					return data['response'].strip()
				return "❌ Неожиданный формат ответа от API"
		except Exception as e:
			return f"❌ Ошибка: {e}"

	async def call_model(self, message: str, temperature: float, system_prompt: str | None = None) -> str:
		"""
		Purpose: Route call to current API (chadgpt/perplexity).
		"""
		if self.current_api == "chadgpt":
			return await self.call_chadgpt(message, temperature, system_prompt)
		return await self.call_perplexity(message, temperature, system_prompt)

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

    # experiment feature removed per request

	def print_ded_message(self, message: str, eff_temp: float | None = None) -> None:
		"""
		Purpose: Pretty-print model message with optional T-indicator.
		In explain_mode, temperature is always shown.
		Args:
			message: Text to print
			eff_temp: Effective temperature indicator
		"""
		# Better readability: wrap to terminal width and add spacing, show model
		width = shutil.get_terminal_size((100, 20)).columns
		prefix = "👴 Дедушка"
		model_label = self.get_model_label()
		if self.explain_mode:
			t = eff_temp if eff_temp is not None else self.default_temperature
			prefix = f"{prefix} [T={t:.2f} • {model_label}]"
		suffix = ""
		if not self.explain_mode:
			# In normal mode, do not show temperature or model
			suffix = ""
		wrapped = textwrap.fill(f"{prefix}: {message}{suffix}", width=width)
		print(wrapped)
		print()

	def get_model_label(self) -> str:
		"""
		Purpose: Human-readable model label for indicators.
		"""
		if self.current_api == "chadgpt":
			return "chadgpt:gpt-5-mini"
		return f"perplexity:{MODEL}"

	def get_api_endpoint(self) -> str:
		"""
		Purpose: Return API endpoint URL for current provider.
		"""
		return CHAD_URL if self.current_api == "chadgpt" else API_URL

	def print_debug_info(self, user_message: str, reply: str, eff_temp: float, sys_prompt: str | None, duration_ms: int) -> None:
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
		lines = [
			"🔍 Debug:",
			f"  api: {self.current_api}",
			f"  endpoint: {endpoint}",
			f"  model: {model_label}",
			f"  temperature: {eff_temp:.2f}",
			f"  mode: {mode}",
			f"  prompt(sys)≈: {prompt_preview}",
			f"  req_len: {len(user_message)} chars",
			f"  resp_len: {len(reply)} chars",
			f"  time: {duration_ms} ms",
		]
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
		self.advice_mode = AdviceMode(self.api_key, self.current_api)
		welcome = await self.call_model("Привет! Дай короткое ехидное приветствие.", self.default_temperature)
		self.print_ded_message(welcome, self.default_temperature)
		self.apply_interactive_temperature(welcome)

		while True:
			user_message = self.get_user_input()
			if not user_message:
				continue

			low = user_message.lower()

			# exit by substring (only "покеда")
			if _contains_any(low, ["покеда"]):
				bye = await self.call_model("Скажи короткое ехидное прощание.", self.default_temperature)
				self.print_ded_message(bye, self.default_temperature)
				self.apply_interactive_temperature(bye)
				break

			# API switching: 'api chadgpt' or 'api perplexity'
			if low.startswith("api "):
				new_api = low.split()[1]
				if new_api in ("chadgpt", "perplexity"):
					if not is_api_key_configured(new_api):
						print(f"❌ API '{new_api}' не настроен. Проверьте ключ.")
						print()
					else:
						self.current_api = new_api
						self.api_key = get_api_key(new_api)
						# Re-init advice mode helper with new API
						self.advice_mode = AdviceMode(self.api_key, self.current_api)
						print(f"👴 Дедушка: Переключаюсь на {new_api}!")
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

			# help by substring
			if "помогай" in low:
				print("🔧 Команды:")
				print("  • temp <value>         — установить температуру по умолчанию (0.0–1.5)")
				print("  • объясняй             — включить режим пояснений (показывать T и модель)")
				print("  • надоел               — выключить режим пояснений")
				print("  • покеда               — завершить разговор")
				print("  • api chadgpt|perplexity — переключить провайдера API")
				print()
				print("📦 Триггеры авто‑температуры (по тексту): ‘не душни’ → 0.0, ‘потише’ → 0.7, ‘разгоняй’ → 1.2")
				print()
				# continue but do not block sending the same message if it has content
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

			# experiment command removed

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


			# unified "надоел" handled above

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
			reply = await self.call_model(user_message, eff)
			duration_ms = int((time.time() - start_ts) * 1000)
			print("\r" + " " * 30 + "\r", end="")
			self.print_ded_message(reply, eff)
			# Debug info (explain mode only)
			self.print_debug_info(user_message, reply, eff, None, duration_ms)
			self.apply_interactive_temperature(reply)


async def main():
	chat = DedChatV4()
	async with chat:
		await chat.run()


if __name__ == "__main__":
	asyncio.run(main())


