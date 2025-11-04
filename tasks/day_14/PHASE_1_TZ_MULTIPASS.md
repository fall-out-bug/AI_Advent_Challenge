# ТЗ: Phase 1 — Multi-Pass Code Review Architecture (Дни 1-8)

## Контекст

Текущая система выполняет **single-pass code review** одним вызовом Mistral. Это ограничивает качество и глубину анализа для больших проектов с multiple компонентами (Docker, Airflow, Spark, MLflow).

**Цель Phase 1**: Реализовать **3-проходный анализ** с сохранением контекста между проходами, что позволит:
- **Pass 1**: Выявить архитектурные проблемы и структуру проекта (5-10 мин)
- **Pass 2**: Провести детальный анализ каждого компонента с использованием findings из Pass 1 (10-15 мин)
- **Pass 3**: Синтезировать финальный отчёт и перекрёстную валидацию (5 мин)

---

## Архитектурный дизайн Phase 1

### Текущее состояние
```
Code Input 
  ↓
CodeReviewerAgent.process() [Single Pass]
  ↓
Mistral API Call
  ↓
Report Output
```

### Целевое состояние Phase 1
```
Code Input 
  ↓
MultiPassReviewerAgent.process_multi_pass()
  ├─ Pass 1: ArchitectureReviewPass
  │   ├─ Parse code structure
  │   ├─ Detect components (Docker, Airflow, Spark, MLflow)
  │   ├─ Build dependency graph
  │   ├─ Call Mistral with "architecture_overview" prompt
  │   └─ Save findings to session_memory
  │
  ├─ Pass 2: ComponentDeepDivePass [per component]
  │   ├─ For each detected component (docker, airflow, spark, mlflow)
  │   ├─ Load context from Pass 1 findings
  │   ├─ Call Mistral with specialized prompt (pass_2_docker.md, etc.)
  │   └─ Save per-component findings to session_memory
  │
  └─ Pass 3: SynthesisPass
      ├─ Load all findings from Pass 1 & Pass 2
      ├─ Call Mistral with "synthesis" prompt
      ├─ Merge and prioritize recommendations
      └─ Generate final structured report
  
  All passes use: SessionManager for findings persistence
```

---

## Файловая структура (что создавать/менять)

```
project/
├── src/
│   ├── domain/
│   │   ├── agents/
│   │   │   ├── multi_pass_reviewer.py (NEW) ✨
│   │   │   │   └── class MultiPassReviewerAgent
│   │   │   │
│   │   │   ├── passes/  (NEW FOLDER) ✨
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_pass.py (NEW) → BaseReviewPass
│   │   │   │   ├── architecture_pass.py (NEW) → ArchitectureReviewPass
│   │   │   │   ├── component_pass.py (NEW) → ComponentDeepDivePass
│   │   │   │   └── synthesis_pass.py (NEW) → SynthesisPass
│   │   │   │
│   │   │   ├── session_manager.py (NEW) ✨
│   │   │   │   └── class SessionManager
│   │   │   │
│   │   │   ├── code_reviewer.py (REFACTOR)
│   │   │   │   └── Keep for backwards compat, mark as @deprecated
│   │   │   │
│   │   │   └── ... (existing)
│   │   │
│   │   ├── models/
│   │   │   ├── code_review_models.py (UPDATE) 
│   │   │   │   ├── Add: PassName enum (PASS_1, PASS_2, PASS_3)
│   │   │   │   ├── Add: PassFindings dataclass
│   │   │   │   ├── Add: MultiPassReport dataclass
│   │   │   │   └── Keep: existing CodeReviewReport
│   │   │   └── ... (existing)
│   │   │
│   │   └── ... (existing)
│   │
│   ├── infrastructure/
│   │   └── ... (existing - no changes)
│   │
│   ├── main.py (REFACTOR)
│   │   └── Add endpoint for multi_pass review
│   │
│   └── ... (existing)
│
├── prompts/
│   ├── v1/
│   │   ├── pass_1_architecture_overview.md (NEW) ✨
│   │   ├── pass_2_docker_review.md (NEW) ✨
│   │   ├── pass_2_airflow_review.md (NEW) ✨
│   │   ├── pass_2_spark_review.md (NEW) ✨
│   │   ├── pass_2_mlflow_review.md (NEW) ✨
│   │   ├── pass_3_synthesis.md (NEW) ✨
│   │   └── prompt_registry.yaml (NEW) → version tracking
│   │
│   └── ... (existing prompts, keep for backwards compat)
│
├── tests/
│   ├── test_multi_pass_reviewer.py (NEW) ✨
│   ├── test_passes/  (NEW FOLDER) ✨
│   │   ├── test_architecture_pass.py (NEW)
│   │   ├── test_component_pass.py (NEW)
│   │   └── test_synthesis_pass.py (NEW)
│   ├── test_session_manager.py (NEW) ✨
│   └── ... (existing tests)
│
├── docs/
│   ├── PHASE_1_IMPLEMENTATION.md (NEW) → implementation notes
│   ├── MULTI_PASS_ARCHITECTURE.md (NEW) → architecture details
│   └── ... (existing)
│
└── ... (root files)
```

---

## Спецификация компонентов Phase 1

### 1. **SessionManager** — Управление состоянием между проходами

**Файл**: `src/domain/agents/session_manager.py`

**Функциональность**:
- Создаёт уникальный session_id для каждого review
- Сохраняет findings каждого прохода (Pass 1, Pass 2_docker, Pass 2_airflow, etc.)
- Загружает findings для использования в контексте следующего прохода
- Persists состояние на диск (JSON files)
- Cleanup старых сессий (> 24 часов)

**API**:
```python
class SessionManager:
    def __init__(self, session_id: str = None):
        # Create new session or load existing
        
    @staticmethod
    def create() -> 'SessionManager':
        # Generate new session_id
        
    def save_findings(self, pass_name: str, findings: Dict[str, Any]) -> None:
        # Save findings with pass_name key
        # Example: pass_name = "pass_1" or "pass_2_docker"
        
    def load_findings(self, pass_name: str) -> Dict[str, Any]:
        # Load findings by pass_name
        # Return {} if not found
        
    def load_all_findings(self) -> Dict[str, Any]:
        # Load all findings from all passes
        
    def get_context_summary_for_next_pass(self) -> str:
        # Generate summarized context for next pass
        # Format: "Previous findings summary in human-readable format"
        
    def persist(self) -> None:
        # Save session state to disk
        
    def cleanup(self) -> None:
        # Delete temporary files

class PassFindings:
    """Data container for findings from each pass"""
    pass_name: str  # e.g., "pass_1", "pass_2_docker"
    timestamp: datetime
    findings: Dict[str, List[str]]  # "critical", "major", "minor" → list of issues
    recommendations: List[str]
    metadata: Dict[str, Any]  # timing, token usage, etc.
```

**Storage**:
- Path: `/tmp/sessions/{session_id}/`
- Files:
  - `findings_pass_1.json`
  - `findings_pass_2_docker.json`
  - `findings_pass_2_airflow.json`
  - `findings_pass_2_spark.json`
  - `findings_pass_2_mlflow.json`
  - `findings_pass_3.json`
  - `session_metadata.json` (timestamps, component types detected, etc.)

---

### 2. **BaseReviewPass** — Абстрактный класс для каждого прохода

**Файл**: `src/domain/agents/passes/base_pass.py`

**Функциональность**:
- Определяет интерфейс для всех passes
- Управляет токен-бюджетом
- Логирует выполнение
- Обработка ошибок

**API**:
```python
class BaseReviewPass(ABC):
    def __init__(
        self,
        mistral_client: UnifiedModelClient,
        session_manager: SessionManager,
        token_budget: int = 2000
    ):
        self.client = mistral_client
        self.session = session_manager
        self.token_budget = token_budget
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def run(self, code: str, **kwargs) -> PassFindings:
        """Execute the pass and return findings"""
    
    async def _call_mistral(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Common method for calling Mistral with error handling"""
        # Log prompt
        self.logger.info(f"Calling Mistral: {prompt[:100]}...")
        
        # Call model
        response = await self.client.send_prompt(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Log response
        self.logger.info(f"Response: {response[:100]}...")
        return response
    
    def _load_prompt_template(self, template_name: str) -> str:
        """Load prompt from prompts/v1/{template_name}.md"""
        # Implementation
    
    def _estimate_tokens(self, text: str) -> int:
        """Quick token count estimate"""
        # Implementation using TokenAnalyzer or rough estimate
```

---

### 3. **ArchitectureReviewPass** — Pass 1 (Архитектурный обзор)

**Файл**: `src/domain/agents/passes/architecture_pass.py`

**Функциональность**:
- Парсит структуру кода
- Выявляет типы компонентов (docker, airflow, spark, mlflow)
- Анализирует зависимости
- Вызывает Mistral с архитектурным промптом
- Сохраняет findings и detected component types

**API**:
```python
class ArchitectureReviewPass(BaseReviewPass):
    async def run(self, code: str) -> PassFindings:
        self.logger.info("Starting Pass 1: Architecture Review")
        
        # 1. Parse code structure
        detected_components = self._detect_components(code)
        self.logger.info(f"Detected components: {detected_components}")
        
        # 2. Build component summary
        component_summary = self._build_component_summary(code, detected_components)
        
        # 3. Load prompt template
        prompt_template = self._load_prompt_template("pass_1_architecture_overview")
        
        # 4. Prepare prompt for Mistral
        prompt = prompt_template.format(
            code_snippet=code[:3000],  # First 3K chars for architecture overview
            component_summary=component_summary,
            detected_components=", ".join(detected_components)
        )
        
        # 5. Call Mistral
        response = await self._call_mistral(
            prompt=prompt,
            temperature=0.5,  # Lower temperature for architecture analysis
            max_tokens=1000
        )
        
        # 6. Parse response
        findings = self._parse_response(response)
        
        # 7. Save session state
        pass_findings = PassFindings(
            pass_name="pass_1",
            timestamp=datetime.now(),
            findings=findings["findings"],
            recommendations=findings["recommendations"],
            metadata={
                "detected_components": detected_components,
                "token_estimate": self._estimate_tokens(prompt)
            }
        )
        
        self.session.save_findings("pass_1", pass_findings.to_dict())
        return pass_findings
    
    def _detect_components(self, code: str) -> List[str]:
        """Detect which component types are present"""
        components = []
        
        if "docker-compose" in code.lower() or "services:" in code:
            components.append("docker")
        
        if "DAG(" in code or "@dag" in code or "airflow" in code.lower():
            components.append("airflow")
        
        if "spark" in code.lower() or "SparkSession" in code or "pyspark" in code.lower():
            components.append("spark")
        
        if "mlflow" in code.lower() or "log_metric" in code:
            components.append("mlflow")
        
        return components if components else ["generic"]
    
    def _build_component_summary(self, code: str, components: List[str]) -> str:
        """Build summary of detected components"""
        summary_lines = []
        for comp in components:
            if comp == "docker":
                services = re.findall(r"^\s+(\w+):", code, re.MULTILINE)
                summary_lines.append(f"Docker services: {', '.join(services)}")
            elif comp == "airflow":
                dags = re.findall(r"(?:@dag|DAG)\(dag_id=['\"](\w+)['\"]", code)
                summary_lines.append(f"Airflow DAGs: {', '.join(dags)}")
            # Similar for spark, mlflow
        
        return "\n".join(summary_lines) if summary_lines else "No specific components detected"
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse Mistral response into structured findings"""
        # Try to parse as JSON first
        try:
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            # Fallback: extract sections manually
            return {
                "findings": {
                    "critical": self._extract_section(response, "CRITICAL"),
                    "major": self._extract_section(response, "MAJOR"),
                    "minor": self._extract_section(response, "MINOR")
                },
                "recommendations": self._extract_section(response, "RECOMMENDATIONS")
            }
    
    def _extract_section(self, text: str, section_name: str) -> List[str]:
        """Extract bullet points from a section"""
        # Implementation
```

---

### 4. **ComponentDeepDivePass** — Pass 2 (Детальный анализ компонентов)

**Файл**: `src/domain/agents/passes/component_pass.py`

**Функциональность**:
- Принимает тип компонента (docker, airflow, spark, mlflow)
- Загружает контекст из Pass 1
- Выбирает специализированный промпт (pass_2_docker.md, etc.)
- Вызывает Mistral с углублённым анализом
- Сохраняет findings для каждого компонента

**API**:
```python
class ComponentDeepDivePass(BaseReviewPass):
    async def run(
        self,
        code: str,
        component_type: str,  # "docker", "airflow", "spark", "mlflow"
        context_from_pass_1: Dict[str, Any] = None
    ) -> PassFindings:
        self.logger.info(f"Starting Pass 2: Component Deep-Dive for {component_type}")
        
        # 1. Load context from Pass 1
        pass_1_context = context_from_pass_1 or self.session.load_findings("pass_1")
        context_summary = self.session.get_context_summary_for_next_pass()
        
        # 2. Extract relevant code for this component
        component_code = self._extract_component_code(code, component_type)
        
        # 3. Load specialized prompt template
        prompt_template = self._load_prompt_template(f"pass_2_{component_type}_review")
        
        # 4. Prepare prompt with context from Pass 1
        prompt = prompt_template.format(
            code_snippet=component_code,
            context_from_pass_1=context_summary,
            component_type=component_type
        )
        
        # 5. Call Mistral
        response = await self._call_mistral(
            prompt=prompt,
            temperature=0.6,
            max_tokens=1500
        )
        
        # 6. Parse response
        findings = self._parse_response(response)
        
        # 7. Save findings
        pass_name = f"pass_2_{component_type}"
        pass_findings = PassFindings(
            pass_name=pass_name,
            timestamp=datetime.now(),
            findings=findings["findings"],
            recommendations=findings["recommendations"],
            metadata={
                "component_type": component_type,
                "token_estimate": self._estimate_tokens(prompt)
            }
        )
        
        self.session.save_findings(pass_name, pass_findings.to_dict())
        return pass_findings
    
    def _extract_component_code(self, code: str, component_type: str) -> str:
        """Extract code relevant to specific component type"""
        if component_type == "docker":
            # Extract docker-compose section
            if "docker-compose" in code.lower():
                return code  # Assume entire code is docker-compose
            # Or extract docker-related lines
        
        elif component_type == "airflow":
            # Extract DAG definitions
            pass
        
        # Similar for spark, mlflow
        
        return code  # Return full code if can't extract
```

---

### 5. **SynthesisPass** — Pass 3 (Синтез и финальный отчёт)

**Файл**: `src/domain/agents/passes/synthesis_pass.py`

**Функциональность**:
- Загружает findings из всех предыдущих проходов
- Синтезирует финальный отчёт
- Проверяет cross-component интеграцию
- Приоритизирует рекомендации

**API**:
```python
class SynthesisPass(BaseReviewPass):
    async def run(self, code: str = None) -> PassFindings:
        self.logger.info("Starting Pass 3: Synthesis & Integration Check")
        
        # 1. Load all findings from previous passes
        all_findings = self.session.load_all_findings()
        
        # 2. Build comprehensive context
        synthesis_context = self._build_synthesis_context(all_findings)
        
        # 3. Load synthesis prompt template
        prompt_template = self._load_prompt_template("pass_3_synthesis")
        
        # 4. Prepare prompt
        prompt = prompt_template.format(
            all_findings_summary=synthesis_context,
            pass_1_findings=all_findings.get("pass_1", {}),
            pass_2_findings=all_findings.get("pass_2", {})  # All pass_2_* combined
        )
        
        # 5. Call Mistral
        response = await self._call_mistral(
            prompt=prompt,
            temperature=0.5,
            max_tokens=2000
        )
        
        # 6. Parse and structure response
        findings = self._parse_response(response)
        
        # 7. Prioritize and merge recommendations
        merged_findings = self._merge_findings(findings, all_findings)
        
        # 8. Save final findings
        pass_findings = PassFindings(
            pass_name="pass_3",
            timestamp=datetime.now(),
            findings=merged_findings["findings"],
            recommendations=merged_findings["recommendations"],
            metadata={
                "passes_merged": list(all_findings.keys()),
                "token_estimate": self._estimate_tokens(prompt)
            }
        )
        
        self.session.save_findings("pass_3", pass_findings.to_dict())
        return pass_findings
    
    def _build_synthesis_context(self, all_findings: Dict[str, Any]) -> str:
        """Build comprehensive summary of all findings"""
        context_parts = []
        
        for pass_name, findings in all_findings.items():
            context_parts.append(f"\n## Findings from {pass_name}:")
            if isinstance(findings, dict):
                context_parts.append(str(findings))
        
        return "\n".join(context_parts)
    
    def _merge_findings(
        self,
        synthesis_findings: Dict[str, Any],
        all_findings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge findings, remove duplicates, prioritize"""
        # Implementation
```

---

### 6. **MultiPassReviewerAgent** — Оркестратор всех проходов

**Файл**: `src/domain/agents/multi_pass_reviewer.py`

**Функциональность**:
- Управляет flow всех трёх проходов
- Оркестрирует вызовы Pass 1 → Pass 2 (per component) → Pass 3
- Формирует финальный MultiPassReport

**API**:
```python
class MultiPassReviewerAgent:
    def __init__(
        self,
        mistral_client: UnifiedModelClient,
        token_budget: int = 8000  # Total budget for all 3 passes
    ):
        self.client = mistral_client
        self.token_budget = token_budget
        self.logger = logging.getLogger(__name__)
    
    async def process_multi_pass(
        self,
        code: str,
        repo_name: str = "student_project"
    ) -> 'MultiPassReport':
        """Main entry point for multi-pass review"""
        
        self.logger.info("Starting multi-pass code review")
        start_time = datetime.now()
        
        # 1. Create session
        session = SessionManager.create()
        self.logger.info(f"Created session: {session.session_id}")
        
        # 2. Pass 1: Architecture Overview
        architecture_pass = ArchitectureReviewPass(
            mistral_client=self.client,
            session_manager=session,
            token_budget=self.token_budget // 3
        )
        pass_1_findings = await architecture_pass.run(code)
        detected_components = pass_1_findings.metadata.get("detected_components", [])
        self.logger.info(f"Pass 1 complete. Detected components: {detected_components}")
        
        # 3. Pass 2: Component Deep-Dives (parallel or sequential)
        pass_2_findings = {}
        component_pass = ComponentDeepDivePass(
            mistral_client=self.client,
            session_manager=session,
            token_budget=self.token_budget // 3
        )
        
        for component_type in detected_components:
            if component_type != "generic":
                self.logger.info(f"Starting Pass 2 for {component_type}")
                findings = await component_pass.run(
                    code=code,
                    component_type=component_type,
                    context_from_pass_1=pass_1_findings.to_dict()
                )
                pass_2_findings[component_type] = findings
                self.logger.info(f"Pass 2 complete for {component_type}")
        
        # 4. Pass 3: Synthesis
        synthesis_pass = SynthesisPass(
            mistral_client=self.client,
            session_manager=session,
            token_budget=self.token_budget // 3
        )
        pass_3_findings = await synthesis_pass.run()
        self.logger.info("Pass 3 complete")
        
        # 5. Build final report
        final_report = MultiPassReport(
            session_id=session.session_id,
            repo_name=repo_name,
            pass_1=pass_1_findings,
            pass_2=pass_2_findings,
            pass_3=pass_3_findings,
            detected_components=detected_components,
            execution_time=(datetime.now() - start_time).total_seconds()
        )
        
        # 6. Persist session
        session.persist()
        
        self.logger.info(f"Multi-pass review complete in {final_report.execution_time:.1f}s")
        return final_report
    
    async def get_report(self, session_id: str) -> 'MultiPassReport':
        """Retrieve existing report by session_id"""
        # Implementation
    
    async def export_report(
        self,
        report: 'MultiPassReport',
        format: str = "markdown"  # or "json", "html"
    ) -> str:
        """Export report to different formats"""
        # Implementation
```

---

### 7. **Data Models** — Обновить models

**Файл**: `src/domain/models/code_review_models.py` (UPDATE)

**Добавить**:
```python
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime

class PassName(Enum):
    PASS_1 = "pass_1"
    PASS_2_DOCKER = "pass_2_docker"
    PASS_2_AIRFLOW = "pass_2_airflow"
    PASS_2_SPARK = "pass_2_spark"
    PASS_2_MLFLOW = "pass_2_mlflow"
    PASS_3 = "pass_3"

@dataclass
class PassFindings:
    pass_name: str
    timestamp: datetime
    findings: Dict[str, List[str]]  # "critical", "major", "minor"
    recommendations: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pass_name": self.pass_name,
            "timestamp": self.timestamp.isoformat(),
            "findings": self.findings,
            "recommendations": self.recommendations,
            "metadata": self.metadata
        }

@dataclass
class MultiPassReport:
    session_id: str
    repo_name: str
    pass_1: PassFindings
    pass_2: Dict[str, PassFindings]  # component_type → findings
    pass_3: PassFindings
    detected_components: List[str]
    execution_time: float  # seconds
    
    def to_markdown(self) -> str:
        """Export report as Markdown"""
        # Implementation
    
    def to_json(self) -> str:
        """Export report as JSON"""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        # Implementation
```

---

## Prompts для Phase 1

Создать 6 новых файлов в `prompts/v1/`:

### **pass_1_architecture_overview.md**
```markdown
# System Prompt
You are an expert software architect reviewing a codebase for architectural issues and structure.

# Task
Analyze the provided code for:
1. Overall architecture and design patterns
2. Component types detected (Docker, Airflow, Spark, MLflow, etc.)
3. High-level dependencies and integrations
4. Potential architectural issues

# Code Structure Summary
{component_summary}

# Detected Components
{detected_components}

# Code to Analyze
{code_snippet}

# Output Format
Return a structured analysis with:
- CRITICAL: Architectural problems that block functionality
- MAJOR: Design issues that impact scalability/maintainability
- MINOR: Code quality suggestions
- RECOMMENDATIONS: Suggested improvements

Return as JSON or clear sections.
```

### **pass_2_docker_review.md**
```markdown
# System Prompt
You are a DevOps expert reviewing Docker and Docker Compose configurations.

# Context from Pass 1
{context_from_pass_1}

# Task
Perform detailed review of Docker configuration:
1. Service dependencies and networking
2. Environment variables and secrets management
3. Volume mounts and data persistence
4. Resource limits (CPU, memory)
5. Security (user, permissions, capabilities)
6. Image optimization (layers, caching, size)
7. Health checks
8. Restart policies

# Docker Configuration
{code_snippet}

# Output Format
```json
{
  "critical": [...],
  "major": [...],
  "minor": [...],
  "recommendations": [...]
}
```

# Checklist
- [ ] All services have health checks
- [ ] Secrets are not in environment variables
- [ ] Resource limits are set
- [ ] Images are pinned to specific versions
- [ ] Multi-stage builds used for optimization
```

### **pass_2_airflow_review.md**
```markdown
# System Prompt
You are an Apache Airflow expert reviewing DAG definitions.

# Context from Pass 1
{context_from_pass_1}

# Task
Perform detailed review of Airflow DAG:
1. Task dependencies and scheduling
2. Error handling and retry policies
3. SLA compliance
4. Parallelization and performance
5. Data handling (XCom, sensor usage)
6. Code reusability and templating
7. Monitoring and alerting

# DAG Code
{code_snippet}

# Output Format
```json
{
  "critical": [...],
  "major": [...],
  "minor": [...],
  "recommendations": [...]
}
```

# Checklist
- [ ] Tasks are idempotent
- [ ] Error handling is defined
- [ ] Resource pools/slots are configured
- [ ] Logging is comprehensive
- [ ] DAG validation passes
```

### **pass_2_spark_review.md**
```markdown
# System Prompt
You are a Spark performance expert reviewing Spark jobs.

# Context from Pass 1
{context_from_pass_1}

# Task
Perform detailed review of Spark job:
1. DataFrame vs RDD usage (prefer DataFrame API)
2. Shuffle operations and partitioning
3. Broadcast variables for large reads
4. Memory management
5. Data type consistency
6. NULL handling
7. Output format and compression
8. Fault tolerance

# Spark Code
{code_snippet}

# Output Format
```json
{
  "critical": [...],
  "major": [...],
  "minor": [...],
  "recommendations": [...]
}
```

# Checklist
- [ ] Using DataFrame API (not RDD)
- [ ] Partitioning strategy is clear
- [ ] Shuffle operations minimized
- [ ] Memory settings appropriate
- [ ] Error handling included
```

### **pass_2_mlflow_review.md**
```markdown
# System Prompt
You are an MLOps expert reviewing MLflow integration.

# Context from Pass 1
{context_from_pass_1}

# Task
Perform detailed review of MLflow usage:
1. Experiment tracking (logging, metrics, params)
2. Artifact management
3. Model versioning
4. Reproducibility (seeds, dependencies)
5. Environment specification
6. Model registry integration
7. Production readiness

# MLflow Code
{code_snippet}

# Output Format
```json
{
  "critical": [...],
  "major": [...],
  "minor": [...],
  "recommendations": [...]
}
```

# Checklist
- [ ] All metrics logged
- [ ] Seeds set for reproducibility
- [ ] Requirements/environment tracked
- [ ] Model artifacts organized
- [ ] Version strategy clear
```

### **pass_3_synthesis.md**
```markdown
# System Prompt
You are a senior software architect synthesizing findings from multiple analysis passes.

# Task
Synthesize findings from all passes:
1. Consolidate duplicate/related findings
2. Prioritize by severity and impact
3. Cross-component validation (how do Docker, Airflow, Spark, MLflow interact?)
4. Identify systemic issues
5. Create actionable recommendations

# Findings from Pass 1 (Architecture Overview)
{pass_1_findings}

# Findings from Pass 2 (Component Analysis)
{pass_2_findings}

# Output Format
Provide final report:
1. EXECUTIVE SUMMARY (1-2 paragraphs)
2. CRITICAL ISSUES (with impact and fix effort)
3. MAJOR ISSUES
4. MINOR ISSUES & IMPROVEMENTS
5. INTEGRATION POINTS & RECOMMENDATIONS
6. PRIORITY ROADMAP (what to fix first)

```json
{
  "executive_summary": "...",
  "critical": [...],
  "major": [...],
  "minor": [...],
  "integration_issues": [...],
  "priority_roadmap": [...]
}
```
```

---

## Testing Requirements

**Файл**: `tests/test_multi_pass_reviewer.py`

```python
@pytest.mark.asyncio
async def test_multi_pass_review_complete_flow():
    """Test full multi-pass review"""
    # Load sample code with all component types
    code = load_sample_project("complete_ml_project")
    
    agent = MultiPassReviewerAgent(mistral_client)
    report = await agent.process_multi_pass(code)
    
    # Assert report structure
    assert report.session_id is not None
    assert report.pass_1 is not None
    assert len(report.pass_2) > 0
    assert report.pass_3 is not None
    assert report.execution_time > 0

@pytest.mark.asyncio
async def test_session_manager_persistence():
    """Test session state is persisted"""
    session = SessionManager.create()
    
    findings_1 = {"critical": ["Issue 1"], "major": []}
    session.save_findings("pass_1", findings_1)
    
    # Load in new instance
    session_2 = SessionManager(session.session_id)
    loaded_findings = session_2.load_findings("pass_1")
    
    assert loaded_findings == findings_1

@pytest.mark.asyncio
async def test_context_passing_between_passes():
    """Test findings are correctly passed between passes"""
    # Implementation
    pass

@pytest.mark.asyncio
async def test_component_detection():
    """Test correct detection of component types"""
    code_with_docker = load_sample_project("docker_only")
    code_with_airflow = load_sample_project("airflow_dag")
    
    # Test detection logic
    pass
```

---

## Timeline для Phase 1

| День | Компонент | Задача | Deliverables |
|------|-----------|--------|--------------|
| 1-2  | SessionManager | Реализовать управление состоянием | session_manager.py, tests |
| 2    | BaseReviewPass | Абстрактный класс для passes | base_pass.py, tests |
| 3    | ArchitectureReviewPass | Pass 1 логика | architecture_pass.py, tests |
| 4    | ComponentDeepDivePass | Pass 2 логика | component_pass.py, tests |
| 4-5  | SynthesisPass | Pass 3 логика | synthesis_pass.py, tests |
| 5-6  | MultiPassReviewerAgent | Оркестратор | multi_pass_reviewer.py, tests |
| 6-7  | Prompts | Все 6 промптов | prompts/v1/*.md |
| 7    | Integration | End-to-end тестирование | integration tests |
| 8    | Documentation | Документация и примеры | PHASE_1_IMPLEMENTATION.md |

---

## Критерии успеха Phase 1

- ✅ Все 3 прохода работают асинхронно
- ✅ Контекст правильно передаётся между проходами
- ✅ Session state persists на диск
- ✅ E2E тест проходит для project со всеми типами компонентов
- ✅ Execution time < 2 минут для типичного project
- ✅ Все промпты работают и выдают структурированный output
- ✅ Документация полная
- ✅ Code quality: 80%+ test coverage, lint clean

---

## Dependency Matrix

```
                     Зависит от
MultiPassReviewerAgent
  └─ ArchitectureReviewPass ─────→ SessionManager, BaseReviewPass
  └─ ComponentDeepDivePass ──────→ SessionManager, BaseReviewPass
  └─ SynthesisPass ──────────────→ SessionManager, BaseReviewPass

BaseReviewPass (abstract)
  └─ UnifiedModelClient (existing)
  └─ Prompts (v1/*.md)

SessionManager (independent)
```

---

## Примечания

1. **Backward compatibility**: Существующие `CodeReviewerAgent` и `single_pass_review` остаются для backwards compatibility, но помечаются как `@deprecated`

2. **Parallel vs Sequential Pass 2**: На Phase 1 можно запускать Pass 2 компоненты sequentially. В Phase 3 (optimization) их можно распараллелить через asyncio.gather()

3. **Token management**: Каждый pass имеет фиксированный token бюджет (total / 3). Если переполнение — логировать warning и truncate

4. **Error handling**: Если один component pass failes — continue с остальными, не блокировать Pass 3

5. **Logging**: Структурированное JSON logging для каждого прохода для debugging и metrics

---

**Готово к передаче в Cursor!**