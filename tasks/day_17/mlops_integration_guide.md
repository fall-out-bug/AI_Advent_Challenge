# Интеграция анализа логов в Code Review Report

## 1. Обзор интеграции

Система анализа логов должна быть встроена как **Pass 4** в существующий multi-pass код-ревью отчет. Результаты анализа добавляются в финальный отчет с информацией о проблемах, выявленных в логах runtime-окружения.

---

## 2. Архитектура интеграции

### 2.1 Модификация существующего pipeline

```
┌─────────────────────────────────────────────────────────┐
│              Code Review Pipeline (Updated)             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Pass 1: Architecture Overview & Static Analysis        │
│         (flake8, pylint, mypy, black, isort)           │
│                          ↓                              │
│  Pass 2: Component Analysis                             │
│         (Docker, Airflow, Spark)                        │
│                          ↓                              │
│  Pass 3: Synthesis & Integration                        │
│         (Combined recommendations)                      │
│                          ↓                              │
│  ★ Pass 4: Runtime Analysis (Logs) [NEW]               │
│         - Parse logs from all components                │
│         - Analyze with local LLM                        │
│         - Classify issues and generate recommendations  │
│                          ↓                              │
│  Final Report Builder                                   │
│  (Merge all passes into single report)                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Структура данных отчета

```python
@dataclass
class CodeReviewReport:
    session_id: str
    created: datetime
    pass_1_results: ArchitectureResults
    pass_2_results: ComponentResults
    pass_3_results: SynthesisResults
    pass_4_results: LogAnalysisResults  # ← NEW
    
    def to_markdown(self) -> str:
        """Экспортировать в Markdown с всеми pass'ами"""
```

---

## 3. Модификация существующего кода

### 3.1 Обновленный main report builder

```python
# report_generator.py (modified)

class MultiPassReportBuilder:
    """Построитель multi-pass отчета с анализом логов."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.pass_1 = None
        self.pass_2 = None
        self.pass_3 = None
        self.pass_4 = None  # NEW: Log analysis
        self.created = datetime.now()
    
    async def run_all_passes(self):
        """Запустить все pass'ы по очереди."""
        
        # Pass 1-3: Static analysis (существующий код)
        self.pass_1 = self._run_pass_1()
        self.pass_2 = self._run_pass_2()
        self.pass_3 = self._run_pass_3()
        
        # Pass 4: NEW - Log analysis
        self.pass_4 = await self._run_pass_4_log_analysis()
        
        return self.build_final_report()
    
    async def _run_pass_4_log_analysis(self) -> dict:
        """
        Запустить анализ логов (новый Pass 4).
        """
        logger.info("Starting Pass 4: Runtime Analysis (Logs)")
        
        from log_analysis.parser import LogParser
        from log_analysis.normalizer import LogNormalizer
        from log_analysis.llm_client import OllamaClient
        
        # Собрать логи
        all_entries = self._collect_logs()
        if not all_entries:
            logger.warning("No logs found, skipping Pass 4")
            return {"status": "no_logs"}
        
        # Нормализовать
        grouped = LogNormalizer.group_by_component_and_severity(all_entries)
        log_groups = LogNormalizer.create_log_groups(grouped)
        log_groups = [g for g in log_groups if g.severity != "info"]
        
        logger.info(f"Found {len(log_groups)} log groups to analyze")
        
        # Анализировать через LLM
        ollama_client = OllamaClient()
        analysis_results = []
        
        for log_group in log_groups:
            result = await ollama_client.analyze_log_group(log_group)
            if result:
                analysis_results.append(result)
        
        return {
            "status": "completed",
            "total_log_entries": len(all_entries),
            "log_groups_analyzed": len(analysis_results),
            "results": analysis_results,
        }
    
    def _collect_logs(self) -> list:
        """Собрать логи из всех доступных источников."""
        from pathlib import Path
        from log_analysis.parser import LogParser
        
        logs_dir = Path(self.repo_path) / "logs"
        if not logs_dir.exists():
            return []
        
        all_entries = []
        
        log_file_handlers = {
            "airflow.log": LogParser.parse_airflow_logs,
            "spark-master.log": LogParser.parse_spark_logs,
            "spark-worker-1.log": LogParser.parse_spark_logs,
            "redis.log": LogParser.parse_redis_logs,
            "minio.log": (lambda x: LogParser.parse_generic_logs(x, "minio")),
            "run_stdout.txt": (lambda x: LogParser.parse_generic_logs(x, "stdout")),
            "run_stderr.txt": (lambda x: LogParser.parse_generic_logs(x, "stderr")),
        }
        
        for filename, handler in log_file_handlers.items():
            filepath = logs_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, "r") as f:
                        entries = handler(f.read())
                        all_entries.extend(entries)
                except Exception as e:
                    logger.warning(f"Error parsing {filename}: {e}")
        
        return all_entries
    
    def build_final_report(self) -> str:
        """Построить финальный отчет со всеми pass'ами."""
        
        report = f"""# Code Review Report: {self.session_id}

**Session ID**: {self.session_id}  
**Created**: {self.created.isoformat()}  
**Execution Time**: {self.execution_time:.1f}s

## Summary

"""
        
        # Summary section
        report += self._build_summary_section()
        
        # Pass 1
        report += "\n## Pass 1: Architecture Overview & Static Analysis\n"
        report += self._format_pass_1()
        
        # Pass 2
        report += "\n## Pass 2: Component Analysis\n"
        report += self._format_pass_2()
        
        # Pass 3
        report += "\n## Pass 3: Synthesis & Integration\n"
        report += self._format_pass_3()
        
        # Pass 4 (NEW)
        if self.pass_4 and self.pass_4.get("status") == "completed":
            report += "\n## Pass 4: Runtime Analysis (Logs)\n"
            report += self._format_pass_4_logs()
        
        report += "\n---\n"
        report += "*Generated by Multi-Pass Code Review System v2.0 with Log Analysis*\n"
        
        return report
    
    def _format_pass_4_logs(self) -> str:
        """Форматировать результаты Pass 4 в Markdown."""
        
        pass_4 = self.pass_4
        results = pass_4.get("results", [])
        
        markdown = f"""
### Summary

- **Log Files Analyzed**: 7
- **Total Log Entries**: {pass_4.get('total_log_entries', 0):,}
- **Issue Groups Found**: {len(results)}
- **Components with Issues**: {self._get_components_with_issues(results)}

"""
        
        # Distribution by severity
        severity_dist = self._count_by_severity(results)
        markdown += "### Issues Distribution by Severity\n\n"
        markdown += "| Severity | Count |\n"
        markdown += "|----------|-------|\n"
        for sev, count in severity_dist.items():
            markdown += f"| **{sev.upper()}** | {count} |\n"
        
        markdown += "\n### Detailed Findings\n"
        
        # Group by component
        by_component = {}
        for result in results:
            comp = result.log_group.component
            if comp not in by_component:
                by_component[comp] = []
            by_component[comp].append(result)
        
        for component in sorted(by_component.keys()):
            markdown += f"\n#### {component.upper()}\n"
            for result in by_component[component]:
                markdown += result.to_markdown()
        
        # Top recommendations
        markdown += "\n### Top Recommendations (Prioritized)\n\n"
        recommendations = self._extract_top_recommendations(results)
        
        for i, (rec, priority) in enumerate(recommendations[:5], 1):
            priority_icon = "🔴" if priority == "critical" else "🟠" if priority == "major" else "🟡"
            markdown += f"{i}. {priority_icon} {rec}\n"
        
        return markdown
    
    def _get_components_with_issues(self, results: list) -> str:
        """Получить список компонентов с проблемами."""
        components = set(r.log_group.component for r in results)
        return ", ".join(sorted(components))
    
    def _count_by_severity(self, results: list) -> dict:
        """Подсчитать проблемы по серьезности."""
        counts = {"critical": 0, "major": 0, "minor": 0, "warning": 0}
        for result in results:
            counts[result.classification] += 1
        return counts
    
    def _extract_top_recommendations(self, results: list) -> list:
        """Извлечь топ рекомендации."""
        rec_dict = {}
        for result in results:
            for rec in result.recommendations:
                priority = result.classification
                if rec not in rec_dict or \
                   self._severity_order(priority) > self._severity_order(rec_dict[rec][1]):
                    rec_dict[rec] = (rec_dict.get(rec, [0])[0] + 1, priority)
        
        return sorted(rec_dict.items(), key=lambda x: -x[1][0])
    
    @staticmethod
    def _severity_order(sev: str) -> int:
        """Преобразовать серьезность в порядок сортировки."""
        order = {"critical": 4, "major": 3, "minor": 2, "warning": 1}
        return order.get(sev, 0)
```

### 3.2 Обновленный CLI

```python
# main.py (modified)

import asyncio
from report_generator import MultiPassReportBuilder

async def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path", help="Path to repository")
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--skip-pass4", action="store_true",
                        help="Skip log analysis (Pass 4)")
    parser.add_argument("--output", default="report.md",
                        help="Output file path")
    
    args = parser.parse_args()
    
    builder = MultiPassReportBuilder(
        session_id=args.session_id,
        repo_path=args.repo_path,
        skip_log_analysis=args.skip_pass4,
    )
    
    report = await builder.run_all_passes()
    
    with open(args.output, "w") as f:
        f.write(report)
    
    print(f"Report saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. Примеры вывода Pass 4

### 4.1 Пример структурированного результата

```markdown
## Pass 4: Runtime Analysis (Logs)

### Summary

- **Log Files Analyzed**: 7
- **Total Log Entries**: 847
- **Issue Groups Found**: 12
- **Components with Issues**: airflow, spark, minio

### Issues Distribution by Severity

| Severity | Count |
|----------|-------|
| **CRITICAL** | 2 |
| **MAJOR** | 5 |
| **MINOR** | 5 |

### Detailed Findings

#### AIRFLOW

##### [CRITICAL] Permission Denied

**Количество ошибок:** 8  
**Первое появление:** 2025-11-03T20:36:40.061565217Z  
**Последнее появление:** 2025-11-03T20:36:41.698018916Z

**Описание проблемы:**
Airflow не может запуститься из-за проблем с разрешениями доступа к директории логов. Процесс не имеет прав на создание необходимых директорий.

**Корневая причина:**
Директория `/opt/airflow/logs/scheduler` не инициализирована должным образом или имеет неправильные права доступа. Пользователь `airflow` не может создавать файлы логов в этой директории из-за недостаточных прав.

**Рекомендации:**
1. В Dockerfile добавить инициализацию директорий: `RUN mkdir -p /opt/airflow/logs && chown -R airflow:0 /opt/airflow/logs`
2. Убедиться, что процесс запускается с правильным пользователем (`airflow`) и группой (`0`)
3. Использовать health check для проверки доступности логов перед запуском Airflow
4. Рассмотреть использование init контейнера для гарантированной инициализации

*Уверенность анализа: 98%*

---

#### SPARK

##### [MAJOR] Native Library Not Available

**Количество ошибок:** 2  
**Первое появление:** 2025-11-03T20:36:38.557149137Z  
**Последнее появление:** 2025-11-03T20:36:38.969623884Z

**Описание проблемы:**
Spark не может загрузить native Hadoop библиотеку для текущей платформы, что приведет к снижению производительности.

**Корневая причина:**
Используется образ Linux/контейнер с Java runtime, но native Hadoop библиотеки (libhadoop.so) не скомпилированы для текущей архитектуры (вероятно docker/linux-amd64).

**Рекомендации:**
1. Установить необходимые build tools и Hadoop native libraries в Dockerfile
2. Использовать официальный Apache Spark образ с предкомпилированными native libraries
3. Рассмотреть использование чистого Java реализации (без оптимизаций native код)

*Уверенность анализа: 92%*

---

### Top Recommendations (Prioritized)

1. 🔴 В Dockerfile добавить инициализацию директорий: `RUN mkdir -p /opt/airflow/logs && chown -R airflow:0 /opt/airflow/logs`
2. 🔴 Убедиться, что процесс запускается с правильным пользователем (`airflow`) и группой (`0`)
3. 🟠 Использовать health check для проверки доступности логов перед запуском Airflow
4. 🟠 Установить необходимые build tools и Hadoop native libraries в Dockerfile
5. 🟡 Рассмотреть использование чистой Java реализации без оптимизаций native код
```

---

## 5. Условия включения Pass 4

Pass 4 должен быть включен, если:

✅ Логи доступны в директории `{repo}/logs`  
✅ Находится хотя бы один лог-файл (*.log, *.txt)  
✅ Ollama доступна на http://localhost:11434  
✅ Модель успешно загружена  

Pass 4 может быть пропущен, если:

❌ Флаг `--skip-pass4` передан  
❌ Нет лог-файлов в репозитории  
❌ Ollama недоступна (graceful degradation)  

---

## 6. Настройки окружения для интеграции

```bash
# .env для report generator

# Log Analysis (Pass 4)
ENABLE_LOG_ANALYSIS=true
LOGS_DIR=./logs
LOG_ANALYSIS_MIN_SEVERITY=WARNING

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=120
OLLAMA_RETRIES=3

# Report generation
REPORT_OUTPUT_DIR=./reports
REPORT_FORMAT=markdown  # or json, both
```

---

## 7. GitHub Actions workflow для CI/CD

```yaml
name: Code Review with Log Analysis

on: [pull_request, push]

jobs:
  code-review:
    runs-on: ubuntu-latest
    
    services:
      ollama:
        image: ollama/ollama:latest
        ports:
          - 11434:11434
        options: >-
          --health-cmd="curl -f http://localhost:11434/api/tags || exit 1"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r log_analysis/requirements.txt
      
      - name: Pull Ollama model
        run: |
          ollama pull mistral
      
      - name: Run multi-pass code review
        run: |
          python main.py . \
            --session-id=${{ github.run_id }} \
            --output=report_${{ github.run_id }}.md
      
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: code-review-report
          path: report_*.md
      
      - name: Comment PR with report
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('report_${{ github.run_id }}.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report.slice(0, 65000)  // GitHub comment limit
            });
```

---

## 8. Метрики и статистика

### 8.1 Полный цикл анализа

```
Pass 1 (Static Analysis):     ~30 сек
Pass 2 (Component Analysis):  ~15 сек
Pass 3 (Synthesis):           ~5 сек
Pass 4 (Log Analysis):        ~45 сек (зависит от количества групп логов)
─────────────────────────────────────
Итого:                        ~95 сек
```

### 8.2 Размеры отчетов

- Pass 1-3 (static): ~50-100 KB Markdown
- Pass 4 (logs): ~20-50 KB Markdown (в зависимости от количества ошибок)
- **Итоговый отчет**: ~100-200 KB

### 8.3 Требования к ресурсам

- **CPU**: 1-2 ядра (для Ollama)
- **RAM**: 4-8 GB (для модели Mistral 7B)
- **Disk**: ~5-10 GB (для модели LLM)

---

## 9. Troubleshooting

| Проблема | Решение |
|----------|---------|
| Ollama недоступна | Pass 4 пропускается, остальные pass'ы работают |
| Модель не загружена | Автоматически загружается при первом запуске |
| Timeout на LLM | Увеличить OLLAMA_TIMEOUT или использовать меньшую модель |
| Недостаточно памяти | Использовать более легкую модель (neural-chat вместо mistral) |
| Логи не найдены | Проверить директорию ./logs и формат файлов |

---

## 10. Масштабирование для больших репозиториев

Для больших репозиториев с огромным количеством логов:

1. **Батчирование**: Обрабатывать логи порциями
2. **Кэширование**: Сохранять результаты анализа в Redis
3. **Асинхронность**: Параллельный анализ нескольких групп логов
4. **Фильтрация**: Анализировать только ERROR и WARNING логи

```python
# Пример конфигурации для больших репозиториев
ENABLE_LOG_ANALYSIS = True
LOG_BATCH_SIZE = 20  # Обрабатывать по 20 групп одновременно
LOG_CACHE_TTL = 3600  # Кэширование на 1 час
LOG_MAX_SEVERITY = "WARNING"  # Только WARNING и выше
```
