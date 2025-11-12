# Архитектурные решения для Phase 1 — Уточнения интеграции

## Контекст задачи

У вас есть существующая архитектура с:
- `shared/shared_package/clients/unified_client.py` (UnifiedModelClient)
- `BaseAgent` с методом `_call_model()`
- `src/domain/messaging/message_schema.py` для моделей
- Существующая структура промптов в `shared/shared_package/config/agents.py`

Нужно интегрировать Phase 1 (multi-pass system) минимальным breaking-change'ов к existing коду.

---

## Рекомендация 1: Интеграция с UnifiedModelClient ✅

### Выбор: **Вариант B + Adapter Pattern**

**Решение**: Создать adapter в BaseReviewPass, который использует UnifiedModelClient напрямую, но обёртывает в адаптер для удобства.

**Почему этот вариант**:
- ✅ Минимальные изменения в BaseAgent
- ✅ Не создаём новые параллельные клиенты
- ✅ Переиспользуем existing инфраструктуру
- ✅ Adapter Pattern разделяет concerns [web:37][web:40]

### Архитектура интеграции

```python
# src/domain/agents/model_client_adapter.py (NEW)

class ModelClientAdapter:
    """
    Адаптер для унификации доступа к UnifiedModelClient в контексте multi-pass review.
    Инкапсулирует детали работы с моделью от Pass логики.
    """

    def __init__(self, unified_client: UnifiedModelClient):
        self.client = unified_client
        self.logger = logging.getLogger(__name__)

    async def send_prompt(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        pass_name: str = "generic"  # For logging/tracking
    ) -> str:
        """
        Unified interface for calling model.
        Handles logging, error handling, token counting.
        """
        self.logger.info(f"[{pass_name}] Calling model with {len(prompt)} chars, max_tokens={max_tokens}")

        try:
            # Use UnifiedModelClient directly
            response = await self.client.send_prompt(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )

            self.logger.info(f"[{pass_name}] Model response: {len(response)} chars")
            return response

        except Exception as e:
            self.logger.error(f"[{pass_name}] Model error: {e}")
            raise

    def estimate_tokens(self, text: str) -> int:
        """Delegate to TokenAnalyzer if available, else rough estimate"""
        # Implementation using existing TokenAnalyzer
        pass
```

### Интеграция в BaseReviewPass

```python
# src/domain/agents/passes/base_pass.py

from src.infrastructure.model_client_adapter import ModelClientAdapter

class BaseReviewPass(ABC):
    def __init__(
        self,
        unified_client: UnifiedModelClient,  # ← Pass directly, not model_client param
        session_manager: SessionManager,
        token_budget: int = 2000
    ):
        self.adapter = ModelClientAdapter(unified_client)  # ← Wrap in adapter
        self.session = session_manager
        self.token_budget = token_budget
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _call_mistral(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Use adapter instead of direct client call"""
        return await self.adapter.send_prompt(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            pass_name=self.__class__.__name__
        )
```

### Зачем этот подход?

1. **Adapter Pattern** — UnifiedModelClient имеет опредёленный interface, BaseReviewPass имеет другие expectations. Adapter переводит одно в другое [web:37][web:40].
2. **Не меняем BaseAgent** — BaseAgent остаётся independent, может использовать свой `_call_model()`.
3. **Переиспользуем UnifiedModelClient** — нет дублирования, всё через shared_package.
4. **Логирование & tracking** — adapter может добавлять pass-specific логирование без изменения BaseAgent.

---

## Рекомендация 2: Расположение Prompts ✅

### Выбор: **Вариант A + B гибридный подход**

**Решение**:
- Создать `prompts/v1/` в **корне проекта** (как в ТЗ)
- Это не конфликтует с `shared/shared_package/config/agents.py`
- Существующие промпты остаются в shared, новые multi-pass промпты в корне

**Почему этот вариант**:
- ✅ Clean separation: shared промпты в shared/, multi-pass в корне
- ✅ Future-proof: если когда-то миграция на shared, легко перенести
- ✅ Версионирование: v1/, v2/, etc. в корне можно легко управлять
- ✅ Разработка: при работе на Phase 1 не трогаем shared/ [web:32][web:34]

### Файловая структура

```
project_root/
├── prompts/  (NEW - Multi-pass specific)
│   ├── v1/
│   │   ├── pass_1_architecture_overview.md
│   │   ├── pass_2_docker_review.md
│   │   ├── pass_2_airflow_review.md
│   │   ├── pass_2_spark_review.md
│   │   ├── pass_2_mlflow_review.md
│   │   ├── pass_3_synthesis.md
│   │   └── prompt_registry.yaml  # Version tracking & metadata
│   │
│   └── v2/  (For future iterations)
│
├── shared/  (Existing - Don't touch for Phase 1)
│   └── shared_package/
│       └── config/
│           └── agents.py  (Existing prompts - keep here)
│
└── ... (rest of project)
```

### PromptRegistry (версионирование)

**Файл**: `prompts/v1/prompt_registry.yaml`

```yaml
version: "1.0"
created_at: "2025-11-03"
author: "mlops_team"
description: "Multi-pass code review prompts for Docker, Airflow, Spark, MLflow"

prompts:
  pass_1_architecture:
    filename: "pass_1_architecture_overview.md"
    description: "High-level architecture analysis"
    created: "2025-11-03"
    checksum: "sha256:abc123..."

  pass_2_docker:
    filename: "pass_2_docker_review.md"
    description: "Detailed Docker/Compose configuration review"
    created: "2025-11-03"
    checksum: "sha256:def456..."

  pass_2_airflow:
    filename: "pass_2_airflow_review.md"
    description: "Apache Airflow DAG analysis"
    created: "2025-11-03"
    checksum: "sha256:ghi789..."

  # ... etc for spark, mlflow

  pass_3_synthesis:
    filename: "pass_3_synthesis.md"
    description: "Final synthesis and integration validation"
    created: "2025-11-03"
    checksum: "sha256:jkl012..."
```

### PromptLoader (для загрузки из корня)

**Файл**: `src/infrastructure/prompt_loader.py` (NEW)

```python
from pathlib import Path
import yaml

class PromptLoader:
    """Load prompts from prompts/v1/ directory"""

    PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts" / "v1"
    REGISTRY_FILE = PROMPTS_DIR / "prompt_registry.yaml"

    @classmethod
    def load_prompt(cls, prompt_name: str) -> str:
        """
        Load prompt by name from registry.
        Example: load_prompt("pass_1_architecture") → loads pass_1_architecture_overview.md
        """
        registry = cls._load_registry()

        if prompt_name not in registry["prompts"]:
            raise ValueError(f"Prompt '{prompt_name}' not found in registry")

        prompt_info = registry["prompts"][prompt_name]
        prompt_file = cls.PROMPTS_DIR / prompt_info["filename"]

        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        with open(prompt_file, 'r') as f:
            return f.read()

    @classmethod
    def _load_registry(cls) -> dict:
        """Load prompt registry"""
        with open(cls.REGISTRY_FILE, 'r') as f:
            return yaml.safe_load(f)

    @classmethod
    def list_prompts(cls) -> List[str]:
        """List all available prompts"""
        registry = cls._load_registry()
        return list(registry["prompts"].keys())
```

### Использование в Pass'ах

```python
# src/domain/agents/passes/architecture_pass.py

from src.infrastructure.prompt_loader import PromptLoader

class ArchitectureReviewPass(BaseReviewPass):
    async def run(self, code: str) -> PassFindings:
        # Load prompt from prompts/v1/
        prompt_template = PromptLoader.load_prompt("pass_1_architecture")

        # Format with variables
        prompt = prompt_template.format(
            code_snippet=code[:3000],
            component_summary=self._build_component_summary(code)
        )

        # Call model
        response = await self._call_mistral(prompt)
        ...
```

### Почему это работает?

1. **Separation of concerns** — multi-pass промпты отдельно от existing prompts
2. **Version control** — prompts/v1/, v2/ можно управлять независимо
3. **Discovery** — PromptRegistry — single source of truth для всех промптов
4. **Future migration** — при необходимости можно запросить из БД вместо файлов
5. **CI/CD friendly** — промпты versioned вместе с кодом

---

## Рекомендация 3: Модели данных ✅

### Выбор: **Вариант A — отдельный файл**

**Решение**: Создать отдельный `src/domain/models/code_review_models.py` (НЕ добавлять в message_schema.py)

**Почему не message_schema.py**:
- ❌ message_schema.py — это для messaging/MCP communication
- ❌ PassFindings, MultiPassReport — это domain models для code review, не messages
- ❌ Смешивание concerns — messaging models и domain models разные сущности [web:32][web:34]

### Архитектура моделей

**Файл**: `src/domain/models/code_review_models.py` (NEW)

```python
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

class PassName(Enum):
    """Enum для identification проходов"""
    PASS_1 = "pass_1"
    PASS_2_DOCKER = "pass_2_docker"
    PASS_2_AIRFLOW = "pass_2_airflow"
    PASS_2_SPARK = "pass_2_spark"
    PASS_2_MLFLOW = "pass_2_mlflow"
    PASS_3 = "pass_3"

class SeverityLevel(Enum):
    """Severity levels for findings"""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"

@dataclass
class Finding:
    """Single finding from code review"""
    severity: SeverityLevel
    title: str
    description: str
    location: Optional[str] = None  # File, line number, etc.
    recommendation: Optional[str] = None
    effort_estimate: Optional[str] = None  # "low", "medium", "high"

@dataclass
class PassFindings:
    """Container for findings from a single pass"""
    pass_name: str  # e.g., "pass_1", "pass_2_docker"
    timestamp: datetime = field(default_factory=datetime.now)
    findings: List[Finding] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "pass_name": self.pass_name,
            "timestamp": self.timestamp.isoformat(),
            "findings": [self._finding_to_dict(f) for f in self.findings],
            "recommendations": self.recommendations,
            "summary": self.summary,
            "metadata": self.metadata
        }

    @staticmethod
    def _finding_to_dict(finding: Finding) -> Dict[str, Any]:
        return {
            "severity": finding.severity.value,
            "title": finding.title,
            "description": finding.description,
            "location": finding.location,
            "recommendation": finding.recommendation,
            "effort_estimate": finding.effort_estimate
        }

    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps(self.to_dict(), indent=2, default=str)

@dataclass
class MultiPassReport:
    """Final report combining findings from all passes"""
    session_id: str
    repo_name: str
    created_at: datetime = field(default_factory=datetime.now)

    # Pass results
    pass_1: Optional[PassFindings] = None
    pass_2_results: Dict[str, PassFindings] = field(default_factory=dict)  # component → findings
    pass_3: Optional[PassFindings] = None

    # Metadata
    detected_components: List[str] = field(default_factory=list)
    execution_time_seconds: float = 0.0
    total_findings: int = 0

    @property
    def critical_count(self) -> int:
        """Count critical issues across all passes"""
        count = 0
        for pass_findings in self._all_findings():
            count += sum(1 for f in pass_findings.findings if f.severity == SeverityLevel.CRITICAL)
        return count

    @property
    def major_count(self) -> int:
        """Count major issues"""
        count = 0
        for pass_findings in self._all_findings():
            count += sum(1 for f in pass_findings.findings if f.severity == SeverityLevel.MAJOR)
        return count

    def _all_findings(self) -> List[PassFindings]:
        """Get all PassFindings from all passes"""
        results = []
        if self.pass_1:
            results.append(self.pass_1)
        results.extend(self.pass_2_results.values())
        if self.pass_3:
            results.append(self.pass_3)
        return results

    def to_markdown(self) -> str:
        """Export report as Markdown"""
        md = f"""# Code Review Report: {self.repo_name}

**Session ID**: {self.session_id}
**Created**: {self.created_at.isoformat()}
**Execution Time**: {self.execution_time_seconds:.1f}s

## Summary
- Detected Components: {', '.join(self.detected_components)}
- Critical Issues: {self.critical_count}
- Major Issues: {self.major_count}
- Total Execution Time: {self.execution_time_seconds:.1f} seconds

## Pass 1: Architecture Overview
{self._pass_to_markdown(self.pass_1)}

## Pass 2: Component Analysis
{self._pass_2_to_markdown()}

## Pass 3: Synthesis & Integration
{self._pass_to_markdown(self.pass_3)}

---
*Generated by Multi-Pass Code Review System v1.0*
"""
        return md

    def _pass_to_markdown(self, pass_findings: Optional[PassFindings]) -> str:
        if not pass_findings:
            return "*(No findings)*"

        md = f"\n### {pass_findings.pass_name}\n\n"
        if pass_findings.summary:
            md += f"**Summary**: {pass_findings.summary}\n\n"

        if pass_findings.findings:
            md += "**Findings**:\n"
            for finding in pass_findings.findings:
                md += f"- [{finding.severity.value.upper()}] {finding.title}: {finding.description}\n"

        if pass_findings.recommendations:
            md += "\n**Recommendations**:\n"
            for rec in pass_findings.recommendations:
                md += f"- {rec}\n"

        return md

    def _pass_2_to_markdown(self) -> str:
        if not self.pass_2_results:
            return "*(No component analysis)*"

        md = ""
        for component_type, findings in self.pass_2_results.items():
            md += f"\n### {component_type.upper()}\n"
            md += self._pass_to_markdown(findings)

        return md

    def to_json(self) -> str:
        """Export as JSON"""
        return json.dumps(self.to_dict(), indent=2, default=str)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "repo_name": self.repo_name,
            "created_at": self.created_at.isoformat(),
            "detected_components": self.detected_components,
            "execution_time_seconds": self.execution_time_seconds,
            "pass_1": self.pass_1.to_dict() if self.pass_1 else None,
            "pass_2": {
                comp: findings.to_dict()
                for comp, findings in self.pass_2_results.items()
            },
            "pass_3": self.pass_3.to_dict() if self.pass_3 else None,
            "summary": {
                "critical_count": self.critical_count,
                "major_count": self.major_count,
                "total_findings": self.total_findings
            }
        }
```

### Почему отдельный файл?

1. **Domain vs Messaging** — это domain models (код review), не communication messages
2. **Scalability** — когда будут другие domain models (например, для RAG Phase 2), легко добавить
3. **Testability** — можно тестировать models независимо
4. **Clarity** — структура проекта отражает архитектуру [web:32][web:33][web:34]

### Структура src/domain/models/

```
src/domain/models/
├── __init__.py
├── code_review_models.py (NEW - Phase 1 models)
└── future_models.py (Placeholder for Phase 2+)

# Когда заведёте RAG (Phase 2):
src/domain/models/
├── __init__.py
├── code_review_models.py (Phase 1)
├── rag_models.py (Phase 2 - embeddings, retrieved docs, etc.)
└── ...
```

---

## Итоговая архитектурная диаграмма Phase 1

```
┌─────────────────────────────────────────────────────────────────┐
│                  MultiPassReviewerAgent                         │
│               (Entry point for multi-pass review)               │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ├─────────────────────────────────────────────────────────┐
           │                                                         │
    ┌──────▼──────┐     ┌────────────────┐      ┌────────────────┐ │
    │  Pass 1     │────▶│ SessionManager │◀─────│  Pass 2        │ │
    │ (Arch)      │     │                │      │ (Components)   │ │
    └─────────────┘     └────────────────┘      └────────────────┘ │
           │                      ▲                      │          │
           │                      │                      │          │
           └──────────────────────┼──────────────────────┘          │
                                  │                                 │
                         Pass findings persist                      │
                                  │                                 │
                    ┌─────────────▼─────────────┐                  │
                    │  Session State (JSON)     │                  │
                    │  /tmp/sessions/{id}/      │                  │
                    └───────────────────────────┘                  │
                                                                    │
    ┌─────────────────────────────────────────────────────────┐   │
    │  Shared Infrastructure (existing)                       │   │
    │  - shared_package/clients/unified_client.py            │   │
    │  - shared_package/config/agents.py (existing prompts)  │   │
    └─────────────────────────────────────────────────────────┘   │
           ▲           ▲           ▲           ▲                   │
           │           │           │           │                   │
    ┌──────┴──┐ ┌──────┴──┐ ┌─────┴───┐ ┌──────┴───┐              │
    │ModelClient    Adapter     PromptLoader   Report              │
    │             (NEW)         (NEW)         Generator             │
    └───────────────────────────────────────────────────────────┘  │
                                                                    │
    ┌─────────────────────────────────────────────────────────┐   │
    │  New Structures (Phase 1)                              │   │
    │  ├── src/infrastructure/model_client_adapter.py       │   │
    │  ├── src/infrastructure/prompt_loader.py              │   │
    │  ├── src/domain/models/code_review_models.py          │   │
    │  ├── src/domain/agents/passes/ (all pass classes)     │   │
    │  ├── src/domain/agents/session_manager.py             │   │
    │  ├── src/domain/agents/multi_pass_reviewer.py         │   │
    │  └── prompts/v1/ (all new prompts)                    │   │
    └─────────────────────────────────────────────────────────┘   │
                                                                    │
└────────────────────────────────────────────────────────────────┘
```

---

## Резюме решений

| Вопрос | Выбор | Причина |
|--------|-------|--------|
| **UnifiedModelClient** | Adapter pattern в BaseReviewPass | Минимум breaking changes, переиспользование existing кода |
| **Расположение prompts** | `prompts/v1/` в корне + PromptRegistry | Clean separation, версионирование, не конфликт с shared |
| **Модели данных** | Отдельный `src/domain/models/code_review_models.py` | Domain models ≠ Messaging models, scalability |

---

## Next Steps

1. **Обновить ТЗ** Phase 1 с этими решениями
2. **Создать** `src/infrastructure/model_client_adapter.py`
3. **Создать** `src/infrastructure/prompt_loader.py`
4. **Создать** `src/domain/models/code_review_models.py`
5. **Создать** `prompts/v1/` структуру
6. Затем реализовать Pass классы с интеграцией

---

**Готово к передаче в Cursor!**
