# Пример реализации: Модули для анализа логов MLOps

## Структура проекта

```
mlops_log_analyzer/
├── log_analysis/
│   ├── __init__.py
│   ├── parser.py           # Парсинг логов
│   ├── normalizer.py       # Нормализация и группировка
│   ├── llm_client.py       # Интеграция с Ollama
│   ├── report_builder.py   # Генерация отчетов
│   └── types.py            # Pydantic модели
├── tests/
│   ├── test_parser.py
│   ├── test_normalizer.py
│   └── test_llm_client.py
├── requirements.txt
├── .env
├── docker-compose.yml      # Для Ollama (опционально)
└── main.py                 # Entry point
```

---

## Код: types.py (Pydantic модели)

```python
"""
Data structures для анализа логов.
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


@dataclass
class LogEntry:
    """Структурированная запись лога."""
    timestamp: str
    level: str  # ERROR, WARNING, INFO, DEBUG
    component: str  # airflow, spark, redis, minio
    message: str
    traceback: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    raw_line: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "component": self.component,
            "message": self.message,
            "traceback": self.traceback,
            "file_path": self.file_path,
            "line_number": self.line_number,
        }


@dataclass
class LogGroup:
    """Группа похожих логов для анализа."""
    component: str
    severity: str  # critical, error, warning
    count: int
    entries: List[LogEntry]
    first_occurrence: str
    last_occurrence: str
    error_pattern: str  # сигнатура ошибки

    def sample_content(self, max_lines: int = 20) -> str:
        """Получить репрезентативный фрагмент логов."""
        lines = []
        for entry in self.entries[:max_lines]:
            lines.append(f"[{entry.timestamp}] {entry.level}: {entry.message}")
            if entry.traceback:
                lines.append(entry.traceback[:500])  # First 500 chars
        return "\n".join(lines)


class LLMAnalysisResult(BaseModel):
    """Результат анализа от LLM."""
    log_group: LogGroup = Field(..., description="Исходная группа логов")
    classification: str = Field(
        ...,
        description="Классификация: critical, major, minor, warning",
        pattern="^(critical|major|minor|warning)$"
    )
    description: str = Field(..., description="Описание проблемы на русском")
    root_cause: str = Field(..., description="Корневая причина на русском")
    recommendations: List[str] = Field(..., description="Список рекомендаций")
    confidence: float = Field(
        ...,
        description="Доверие к анализу (0.0-1.0)",
        ge=0.0,
        le=1.0
    )

    class Config:
        arbitrary_types_allowed = True

    def to_markdown(self) -> str:
        """Преобразовать результат в Markdown."""
        md = f"""
### [{self.classification.upper()}] {self.log_group.component}

**Количество ошибок:** {self.log_group.count}
**Первое появление:** {self.log_group.first_occurrence}
**Последнее появление:** {self.log_group.last_occurrence}

**Описание проблемы:**
{self.description}

**Корневая причина:**
{self.root_cause}

**Рекомендации:**
"""
        for i, rec in enumerate(self.recommendations, 1):
            md += f"\n{i}. {rec}"

        md += f"\n\n*Уверенность анализа: {self.confidence:.0%}*\n"
        return md
```

---

## Код: parser.py (Парсинг логов)

```python
"""
Парсинг логов из различных источников.
"""
import re
from typing import List, Tuple
from datetime import datetime
from .types import LogEntry

import logging

logger = logging.getLogger(__name__)


class LogParser:
    """Парсер логов для различных компонентов."""

    # Регулярные выражения
    AIRFLOW_LOG_PATTERN = re.compile(
        r"^(\w+-\d+)\s*\|\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(.+)$"
    )
    SPARK_LOG_PATTERN = re.compile(
        r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)?\s*(\d+)/(\d+)\s+(\d{2}:\d{2}:\d{2})\s+(WARN|ERROR|INFO|DEBUG)\s+(\S+):\s+(.+)$"
    )
    ERROR_LEVEL_KEYWORDS = {
        "ERROR": ["error", "exception", "traceback", "failed", "unable", "cannot"],
        "WARNING": ["warn", "warning", "deprecated", "could not"],
        "INFO": ["info", "started", "initialized", "registered"],
    }

    @staticmethod
    def parse_airflow_logs(content: str) -> List[LogEntry]:
        """
        Парсить логи Airflow с форматом:
        airflow-1 | 2025-11-03T20:36:40.060803460Z Unable to load the config...
        """
        entries = []
        lines = content.split("\n")
        current_traceback = []
        last_entry = None

        for line in lines:
            if not line.strip():
                continue

            match = LogParser.AIRFLOW_LOG_PATTERN.match(line)

            if match:
                # Сохранить предыдущую запись с трейсбэком
                if last_entry and current_traceback:
                    last_entry.traceback = "\n".join(current_traceback)
                    current_traceback = []

                component, timestamp, message = match.groups()
                level = LogParser._detect_level(message)

                entry = LogEntry(
                    timestamp=timestamp,
                    level=level,
                    component=component.lower(),
                    message=message[:200],  # First 200 chars
                    raw_line=line
                )
                entries.append(entry)
                last_entry = entry
            else:
                # Это продолжение трейсбэка
                if last_entry:
                    current_traceback.append(line)

        # Сохранить последний трейсбэк
        if last_entry and current_traceback:
            last_entry.traceback = "\n".join(current_traceback)

        logger.debug(f"Parsed {len(entries)} Airflow log entries")
        return entries

    @staticmethod
    def parse_spark_logs(content: str) -> List[LogEntry]:
        """
        Парсить логи Spark с форматом:
        25/11/03 20:36:37 WARN NativeCodeLoader: Unable to load native-hadoop library
        """
        entries = []

        # Более гибкий парсер для Spark
        spark_pattern = re.compile(
            r"(\d{2}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})\s+(WARN|ERROR|INFO|DEBUG)\s+(\w+):\s+(.+)"
        )

        for line in content.split("\n"):
            if not line.strip():
                continue

            match = spark_pattern.search(line)
            if match:
                timestamp_str, level, component, message = match.groups()

                # Нормализовать timestamp
                timestamp = f"2025-{timestamp_str}"  # Assume 2025

                entry = LogEntry(
                    timestamp=timestamp,
                    level=level,
                    component=f"spark-{component.lower()}",
                    message=message[:200],
                    raw_line=line
                )
                entries.append(entry)
            else:
                logger.debug(f"Could not parse Spark line: {line[:80]}")

        logger.debug(f"Parsed {len(entries)} Spark log entries")
        return entries

    @staticmethod
    def parse_redis_logs(content: str) -> List[LogEntry]:
        """Парсить логи Redis."""
        entries = []

        redis_pattern = re.compile(
            r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)?\s+\d+:\w\s+(\d{2}\s+\w+\s+\d{4})\s+(\d{2}:\d{2}:\d{2}\.\d+)\s+([\w*#]+)\s+(.+)"
        )

        for line in content.split("\n"):
            if not line.strip():
                continue

            if "Warning" in line or "warning" in line:
                level = "WARNING"
            elif "Error" in line or "error" in line:
                level = "ERROR"
            else:
                level = "INFO"

            entry = LogEntry(
                timestamp=datetime.now().isoformat(),
                level=level,
                component="redis",
                message=line[:200],
                raw_line=line
            )
            entries.append(entry)

        return entries

    @staticmethod
    def parse_generic_logs(content: str, service_name: str) -> List[LogEntry]:
        """Универсальный парсер для других логов."""
        entries = []

        for line in content.split("\n"):
            if not line.strip():
                continue

            level = LogParser._detect_level(line)

            entry = LogEntry(
                timestamp=datetime.now().isoformat(),
                level=level,
                component=service_name.lower(),
                message=line[:200],
                raw_line=line
            )
            entries.append(entry)

        return entries

    @staticmethod
    def _detect_level(text: str) -> str:
        """Определить уровень логирования по содержимому."""
        text_lower = text.lower()

        if any(kw in text_lower for kw in LogParser.ERROR_LEVEL_KEYWORDS["ERROR"]):
            return "ERROR"
        elif any(kw in text_lower for kw in LogParser.ERROR_LEVEL_KEYWORDS["WARNING"]):
            return "WARNING"
        else:
            return "INFO"

    @staticmethod
    def extract_error_signature(entry: LogEntry) -> str:
        """Создать сигнатуру ошибки для группировки."""
        # Убрать переменные части из сообщения
        msg = entry.message
        msg = re.sub(r"'/[^']*'", "'{path}'", msg)
        msg = re.sub(r"\d+", "{N}", msg)
        return msg[:100]
```

---

## Код: llm_client.py (Интеграция с Ollama)

```python
"""
Клиент для взаимодействия с локальной LLM через Ollama.
"""
import aiohttp
import asyncio
import json
import logging
from typing import Optional
from .types import LogGroup, LLMAnalysisResult

logger = logging.getLogger(__name__)


class OllamaClient:
    """Асинхронный клиент для Ollama."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "mistral",
        timeout: int = 120,
        retries: int = 3,
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.retries = retries

    async def is_healthy(self) -> bool:
        """Проверить доступность Ollama."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def analyze_log_group(self, log_group: LogGroup) -> Optional[LLMAnalysisResult]:
        """
        Анализировать группу логов через LLM.

        Args:
            log_group: Группа логов для анализа

        Returns:
            LLMAnalysisResult или None если анализ не удался
        """
        prompt = self._build_prompt(log_group)

        for attempt in range(self.retries):
            try:
                response = await self._call_ollama(prompt)
                result = self._parse_response(response, log_group)

                if result:
                    logger.info(
                        f"Successfully analyzed {log_group.component} "
                        f"({log_group.count} errors)"
                    )
                    return result
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{self.retries} failed: {e}"
                )
                if attempt < self.retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        logger.error(f"Failed to analyze log group after {self.retries} retries")
        return None

    def _build_prompt(self, log_group: LogGroup) -> str:
        """Построить prompt для LLM."""
        sample_logs = log_group.sample_content(max_lines=15)

        prompt = f"""Ты — эксперт по MLOps, Docker и отладке распределенных систем.

Проанализируй следующие логи ошибок из компонента '{log_group.component}':
Всего найдено {log_group.count} похожих ошибок.
Первая ошибка: {log_group.first_occurrence}
Последняя ошибка: {log_group.last_occurrence}

=== ЛОГИ ===
{sample_logs}
=== КОНЕЦ ЛОГОВ ===

Дай ответ ТОЛЬКО в формате JSON (без доп. текста):
{{
  "classification": "critical|major|minor|warning",
  "description": "Краткое описание проблемы на русском (1-2 предложения)",
  "root_cause": "Анализ корневой причины на русском (2-3 предложения)",
  "recommendations": [
    "Конкретная рекомендация 1",
    "Конкретная рекомендация 2",
    "Конкретная рекомендация 3"
  ],
  "confidence": 0.85
}}

Требования:
- Ответ ТОЛЬКО JSON
- Все текст на русском языке
- Рекомендации конкретные и actionable
- classification: выбрать одно из [critical, major, minor, warning]
"""
        return prompt

    async def _call_ollama(self, prompt: str) -> str:
        """Отправить запрос в Ollama."""
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.3,  # Low temperature for consistency
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Ollama returned status {resp.status}")

                data = await resp.json()
                return data.get("response", "")

    def _parse_response(
        self,
        response: str,
        log_group: LogGroup
    ) -> Optional[LLMAnalysisResult]:
        """Парсить ответ от LLM."""
        try:
            # Извлечь JSON из ответа
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                logger.warning("No JSON found in LLM response")
                return None

            json_str = json_match.group(0)
            data = json.loads(json_str)

            # Валидировать через Pydantic
            result = LLMAnalysisResult(
                log_group=log_group,
                classification=data.get("classification", "minor"),
                description=data.get("description", ""),
                root_cause=data.get("root_cause", ""),
                recommendations=data.get("recommendations", []),
                confidence=float(data.get("confidence", 0.5))
            )
            return result

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            logger.debug(f"Raw response: {response[:200]}")
            return None

import re
```

---

## Код: normalizer.py (Группировка и дедупликация)

```python
"""
Нормализация логов и группировка для анализа.
"""
from typing import List, Dict
from collections import defaultdict
from .types import LogEntry, LogGroup
from .parser import LogParser
import logging

logger = logging.getLogger(__name__)


class LogNormalizer:
    """Нормализация и группировка логов."""

    @staticmethod
    def group_by_component_and_severity(
        entries: List[LogEntry]
    ) -> Dict[str, List[LogEntry]]:
        """Группировать логи по компоненту и серьезности."""
        grouped = defaultdict(list)

        for entry in entries:
            key = f"{entry.component}_{entry.level}"
            grouped[key].append(entry)

        return dict(grouped)

    @staticmethod
    def create_log_groups(
        grouped_entries: Dict[str, List[LogEntry]]
    ) -> List[LogGroup]:
        """
        Создать группы логов, объединяя похожие ошибки.
        """
        log_groups = []

        for key, entries in grouped_entries.items():
            component, severity = key.rsplit("_", 1)

            # Группировать по сигнатуре ошибки
            by_signature = defaultdict(list)
            for entry in entries:
                sig = LogParser.extract_error_signature(entry)
                by_signature[sig].append(entry)

            # Создать группу для каждой уникальной ошибки
            for signature, sig_entries in by_signature.items():
                # Skip очень часто встречающиеся INFO логи
                if severity == "INFO" and len(sig_entries) > 100:
                    logger.debug(f"Skipping {len(sig_entries)} INFO logs")
                    continue

                group = LogGroup(
                    component=component,
                    severity=LogNormalizer._classify_severity(severity),
                    count=len(sig_entries),
                    entries=sig_entries[:20],  # Keep only first 20 for analysis
                    first_occurrence=sig_entries[0].timestamp,
                    last_occurrence=sig_entries[-1].timestamp,
                    error_pattern=signature,
                )
                log_groups.append(group)

        # Sort by severity
        severity_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
        log_groups.sort(
            key=lambda g: (
                severity_order.get(g.severity, 4),
                -g.count  # More frequent first
            )
        )

        return log_groups

    @staticmethod
    def _classify_severity(level: str) -> str:
        """Преобразовать уровень лога в severity."""
        mapping = {
            "ERROR": "error",
            "WARNING": "warning",
            "INFO": "info",
            "DEBUG": "debug",
        }
        return mapping.get(level, "info")

    @staticmethod
    def filter_relevant_logs(
        entries: List[LogEntry],
        min_severity: str = "WARNING"
    ) -> List[LogEntry]:
        """Фильтровать логи по серьезности."""
        severity_levels = {
            "ERROR": 3,
            "WARNING": 2,
            "INFO": 1,
            "DEBUG": 0,
        }

        min_level = severity_levels.get(min_severity, 2)

        return [
            entry for entry in entries
            if severity_levels.get(entry.level, 0) >= min_level
        ]
```

---

## Код: report_builder.py (Генерация отчетов)

```python
"""
Построение финального отчета анализа логов.
"""
from typing import List
from datetime import datetime
from .types import LLMAnalysisResult
import json
import logging

logger = logging.getLogger(__name__)


class ReportBuilder:
    """Построение отчетов анализа."""

    def __init__(self, analysis_results: List[LLMAnalysisResult]):
        self.results = analysis_results
        self.timestamp = datetime.now().isoformat()

    def build_markdown_report(self) -> str:
        """Построить Markdown отчет."""
        report = f"""# Отчет анализа логов (Log Analysis Report)

**Время анализа:** {self.timestamp}
**Всего найдено проблем:** {len(self.results)}

## Краткое резюме (Summary)

"""
        # Summary statistics
        severity_counts = self._count_by_severity()
        for severity, count in severity_counts.items():
            report += f"- **{severity.upper()}:** {count}\n"

        report += "\n## Проблемы по компонентам (Issues by Component)\n"

        # Group by component
        by_component = {}
        for result in self.results:
            comp = result.log_group.component
            if comp not in by_component:
                by_component[comp] = []
            by_component[comp].append(result)

        for component, results in sorted(by_component.items()):
            report += f"\n### {component.upper()}\n\n"
            for result in results:
                report += result.to_markdown()
                report += "\n---\n"

        # Top recommendations
        report += "\n## Топ рекомендации (Top Recommendations)\n\n"
        all_recs = {}
        for result in self.results:
            for rec in result.recommendations:
                all_recs[rec] = all_recs.get(rec, 0) + 1

        for i, (rec, count) in enumerate(
            sorted(all_recs.items(), key=lambda x: -x[1])[:10],
            1
        ):
            report += f"{i}. {rec}\n"

        return report

    def build_json_report(self) -> str:
        """Построить JSON отчет."""
        data = {
            "timestamp": self.timestamp,
            "total_issues": len(self.results),
            "severity_distribution": self._count_by_severity(),
            "issues": [
                {
                    "component": r.log_group.component,
                    "classification": r.classification,
                    "count": r.log_group.count,
                    "description": r.description,
                    "root_cause": r.root_cause,
                    "recommendations": r.recommendations,
                    "confidence": r.confidence,
                }
                for r in self.results
            ]
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _count_by_severity(self) -> dict:
        """Подсчитать по серьезности."""
        counts = {
            "critical": 0,
            "major": 0,
            "minor": 0,
            "warning": 0,
        }
        for result in self.results:
            counts[result.classification] += 1
        return counts

    def get_action_items(self) -> List[str]:
        """Получить список задач для исправления."""
        items = []

        for result in self.results:
            if result.classification in ["critical", "major"]:
                for rec in result.recommendations:
                    items.append(f"[{result.log_group.component}] {rec}")

        return items
```

---

## Код: main.py (Entry Point)

```python
"""
Главный скрипт для анализа логов.
"""
import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

from log_analysis.parser import LogParser
from log_analysis.normalizer import LogNormalizer
from log_analysis.llm_client import OllamaClient
from log_analysis.report_builder import ReportBuilder

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


async def main():
    """Главная функция."""

    # Конфигурация
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "mistral")
    logs_dir = Path(os.getenv("LOGS_DIR", "./logs"))

    logger.info(f"Starting log analysis with model: {ollama_model}")

    # 1. Инициализировать Ollama клиент
    ollama_client = OllamaClient(
        base_url=ollama_url,
        model=ollama_model
    )

    # Проверить здоровье Ollama
    is_healthy = await ollama_client.is_healthy()
    if not is_healthy:
        logger.error("Ollama is not available!")
        return

    logger.info("✓ Ollama is healthy")

    # 2. Парсить логи
    all_entries = []

    log_files = {
        "airflow.log": LogParser.parse_airflow_logs,
        "spark-master.log": LogParser.parse_spark_logs,
        "spark-worker-1.log": LogParser.parse_spark_logs,
        "redis.log": LogParser.parse_redis_logs,
        "minio.log": (lambda content: LogParser.parse_generic_logs(content, "minio")),
    }

    for filename, parser_func in log_files.items():
        filepath = logs_dir / filename
        if filepath.exists():
            logger.info(f"Parsing {filename}...")
            with open(filepath, "r") as f:
                entries = parser_func(f.read())
                all_entries.extend(entries)
                logger.info(f"  → Found {len(entries)} entries")

    logger.info(f"Total entries parsed: {len(all_entries)}")

    # 3. Нормализовать и сгруппировать
    grouped = LogNormalizer.group_by_component_and_severity(all_entries)
    log_groups = LogNormalizer.create_log_groups(grouped)

    # Фильтровать только релевантные логи
    log_groups = [
        g for g in log_groups
        if g.severity in ["critical", "error", "warning"]
    ]

    logger.info(f"Created {len(log_groups)} log groups for analysis")

    # 4. Анализировать через LLM
    analysis_results = []

    for i, log_group in enumerate(log_groups, 1):
        logger.info(
            f"Analyzing group {i}/{len(log_groups)}: "
            f"{log_group.component} ({log_group.count} errors)"
        )

        result = await ollama_client.analyze_log_group(log_group)
        if result:
            analysis_results.append(result)

        # Небольшая задержка между запросами
        await asyncio.sleep(0.5)

    logger.info(f"Successfully analyzed {len(analysis_results)} groups")

    # 5. Построить отчет
    report_builder = ReportBuilder(analysis_results)

    markdown_report = report_builder.build_markdown_report()
    json_report = report_builder.build_json_report()

    # Сохранить отчеты
    output_dir = Path("./reports")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "log_analysis_report.md", "w") as f:
        f.write(markdown_report)

    with open(output_dir / "log_analysis_report.json", "w") as f:
        f.write(json_report)

    logger.info("Reports saved to ./reports/")
    logger.info(f"\nMarkdown Report Preview:\n{markdown_report[:500]}...")

    # Вывести action items
    action_items = report_builder.get_action_items()
    if action_items:
        logger.info("\n=== ACTION ITEMS ===")
        for item in action_items:
            logger.info(f"  ☐ {item}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Код: requirements.txt

```txt
aiohttp==3.9.0
pydantic==2.5.0
python-dotenv==1.0.0
pytest==7.4.0
pytest-asyncio==0.21.1
httpx==0.25.1
```

---

## Код: .env

```bash
# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=120
OLLAMA_RETRIES=3

# Log analysis
LOGS_DIR=./logs
LOG_ANALYSIS_MIN_SEVERITY=WARNING
```

---

## Код: docker-compose.yml (для локального тестирования)

```yaml
version: "3.8"

services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_MODELS=/root/.ollama/models
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 5
    command: serve

volumes:
  ollama_data:
```

---

## Команды для использования

```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить Ollama (в отдельном терминале)
docker-compose up -d ollama

# Загрузить модель (первый раз)
ollama pull mistral

# Запустить анализ
python main.py

# Запустить тесты
pytest tests/ -v
```

Этот код готов к использованию и может быть дополнен в реальном проекте.
