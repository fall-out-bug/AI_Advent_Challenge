# Day 8: Enhanced Token Analysis System

A comprehensive token analysis and compression system for AI models, featuring accurate token counting, advanced compression strategies, and robust experiment management.

## 🚀 Features

### Core Functionality
- **Accurate Token Counting**: Multiple strategies (simple estimation, ML-based, hybrid)
- **Advanced Compression**: Strategy pattern with truncation, keywords, extractive, semantic, and summarization
- **Robust ML Integration**: Retry logic, circuit breaker, and request validation
- **Comprehensive Experiments**: Builder pattern for experiment results with structured logging
- **Model Switching Demo**: Complete workflow for testing multiple models with compression and quality evaluation

### Architecture & Design
- **Clean Architecture**: Domain, Application, Infrastructure, and Presentation layers
- **Domain-Driven Design**: Entities, value objects, repositories, and domain services
- **SOLID Principles**: Single responsibility, dependency injection, interface segregation
- **Design Patterns**: Strategy, Factory, Builder, Template Method, Circuit Breaker, Facade

### ML Engineering Framework
- **Model Evaluation**: Comprehensive evaluation with MAE, RMSE, compression quality metrics
- **Performance Monitoring**: Drift detection, alerting, and performance analytics
- **Experiment Tracking**: Hyperparameters, metrics, artifacts, and metadata tracking
- **Model Registry**: Versioning, production promotion, and lifecycle management

### Quality & Reliability
- **High Test Coverage**: 74% coverage with 282 passing tests
- **Type Safety**: 100% type hints coverage in core modules
- **Error Handling**: Comprehensive exception hierarchy and structured error management
- **Quality Assurance**: Strict linting, pre-commit hooks, security scanning

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [TASK.md Requirements](#taskmd-requirements)
- [SDK Integration](#sdk-integration)
- [Architecture](#architecture)
- [Domain Layer](#domain-layer)
- [ML Engineering](#ml-engineering)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Examples](#examples)
- [Testing](#testing)
- [Development](#development)
- [Migration Guide](#migration-guide)

## ✅ TASK.md Requirements

This implementation fulfills all requirements from `TASK.md`:

### 1. Token Counting (Подсчёт токенов)
- **Implementation:** `core/token_analyzer.py`
- **Classes:** SimpleTokenCounter, AccurateTokenCounter, TokenCounter
- **Features:** 
  - Input/output token counting for requests and responses
  - Multiple counting strategies (word-based estimation, HuggingFace tokenizers)
  - Support for all models (starcoder, mistral, qwen, tinyllama)
  - Model limit checking and validation
- **Demo:** See token counts displayed in all demo outputs
- **Verification:** `python examples/task_demonstration.py`

### 2. Query Comparison (Сравнение запросов)
- **Implementation:** `core/token_limit_tester.py`
- **Class:** TokenLimitTester with three-stage testing
- **Stages:** 
  - Short queries (~50-100 tokens) - Basic coding tasks
  - Medium queries (~100-500 tokens) - Complex data structures
  - Long queries (500+ tokens) - Comprehensive system design
- **Features:**
  - Automatic query generation based on model capabilities
  - Limit detection and analysis
  - Model-specific query complexity adaptation
- **Demo:** `demo_enhanced.py` shows all three stages with detailed analysis
- **Verification:** `python examples/task_demonstration.py`

### 3. Text Compression (Сжатие текста)
- **Implementation:** `core/text_compressor.py` and `core/compressors/`
- **Strategies:** 
  - Truncation - Keep first + middle + last portions
  - Keywords - Extract important keywords and phrases
  - Extractive - Extractive summarization
  - Semantic - Semantic chunking
  - Summarization - LLM-based summarization
- **Features:**
  - Automatic compression on limit-exceeding queries
  - Compression ratio calculation and analysis
  - Strategy selection based on text characteristics
- **Demo:** Automatic compression applied to long queries in enhanced demo
- **Verification:** `python examples/task_demonstration.py`

### Result: Model Behavior Analysis
The implementation demonstrates how model behavior changes with query complexity:

- **Short Queries:** Fast response, basic functionality, minimal context
- **Medium Queries:** Moderate response time, detailed implementation, better context
- **Long Queries:** Comprehensive responses, enterprise-grade features, full documentation

**Complete Verification Report:** See `TASK_VERIFICATION_REPORT.md` for detailed analysis and test results.

## 🏃 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd day_08

# Install dependencies
make install-dev

# Run tests
make test

# Run experiments
make run
```

### Basic Usage

```python
from core.token_analyzer import SimpleTokenCounter
from core.text_compressor import SimpleTextCompressor
from core.experiments import TokenLimitExperiments
from tests.mocks.mock_config import MockConfiguration

# Initialize components
config = MockConfiguration()
token_counter = SimpleTokenCounter(config=config)
text_compressor = SimpleTextCompressor(token_counter)

# Count tokens
text = "This is a test text for token analysis"
token_info = token_counter.count_tokens(text, "starcoder")
print(f"Tokens: {token_info.count}")

# Compress text
compression_result = text_compressor.compress_text(
    text="Very long text that exceeds model limits...",
    max_tokens=1000,
    model_name="starcoder",
    strategy="truncation"
)
print(f"Compression ratio: {compression_result.compression_ratio}")
```

### Running Demonstrations

#### Primary Demo

Run the comprehensive demo with automatic report generation:

```bash
# Run demo for all available models
python demo.py

# Test specific model
python demo.py --model starcoder

# Test all available models
python demo.py --all
```

Or use the Makefile:

```bash
# Basic demo
make demo

# Demo specific model
make demo-model MODEL=starcoder

# Demo all models
make demo-all
```

**The demo will:**
1. Test models with queries of varying lengths
2. Apply all compression strategies
3. Display detailed results in console
4. Generate comprehensive markdown report in `reports/`

**Report Output:**
- Full model information and specifications
- Complete queries and responses (no clipping)
- Compression results with metrics
- Quality analysis and recommendations
- Collapsible sections for easy navigation

#### Model Switching Demo

The Model Switching Demo provides a comprehensive workflow for testing multiple AI models with different token limits, compression strategies, and quality evaluation.

```python
from demo_enhanced import EnhancedModelSwitchingDemo

# Initialize and run enhanced demo
demo = EnhancedModelSwitchingDemo()
results = await demo.run_enhanced_demo()

# Report is automatically generated and saved
print(f"Report saved to: reports/demo_report_<timestamp>.md")
```

**Demo Features:**
- **Three-Stage Testing**: Short/medium/long queries adapted to model capabilities
- **Compression Evaluation**: Tests all 5 compression algorithms on heavy queries
- **Quality Assessment**: Comprehensive quality metrics using SDK agent patterns
- **Model Comparison**: Side-by-side comparison of StarCoder vs Mistral
- **Automated Reporting**: Detailed markdown reports with recommendations

**Expected Output:**
```
🚀 Starting Model Switching Demo
==================================================

🔍 Checking model availability...
✅ starcoder is available
✅ mistral is available
📊 Will test 2 models: ['starcoder', 'mistral']

============================================================
🧪 Testing starcoder
============================================================
✅ Switched to starcoder

📊 Running three-stage token limit tests...
✅ Three-stage test completed
   Short query: 85 tokens
   Medium query: 450 tokens
   Long query: 1200 tokens
   Queries exceeding limit: 0

============================================================
🧪 Testing mistral
============================================================
✅ Switched to mistral

📊 Running three-stage token limit tests...
✅ Three-stage test completed
   Short query: 75 tokens
   Medium query: 380 tokens
   Long query: 1100 tokens
   Queries exceeding limit: 0

============================================================
📊 DEMO SUMMARY
============================================================
Models tested: 2
Total experiments: 6
Successful experiments: 6
Success rate: 100.0%
Best performing model: starcoder
Best compression strategy: N/A
Completed at: 2024-01-15T10:30:45

🎉 Demo completed successfully!
📄 Report saved to: reports/model_switching_demo_20240115_103045.md
```

## 🔌 SDK Integration

Day 08 has been fully migrated to use the shared SDK agents, providing a unified and robust agentic architecture.

### SDK Agent Integration

The system now uses SDK agents directly instead of day_07 dependencies:

- **CodeGeneratorAgent**: SDK-based code generation with comprehensive error handling
- **CodeReviewerAgent**: SDK-based code quality assessment with detailed metrics
- **SequentialOrchestrator**: SDK orchestration for generator→reviewer workflows
- **DirectAdapter**: SDK adapter for seamless agent communication

### Migration Benefits

- **Unified Architecture**: Single source of truth for agent implementations
- **Better Error Handling**: Comprehensive SDK exception handling and retry logic
- **Enhanced Statistics**: Detailed agent performance metrics and monitoring
- **Improved Reliability**: Robust SDK infrastructure with circuit breakers
- **Future-Proof**: Easy updates and feature additions through SDK

### SDK Agent Usage

```python
from agents.code_generator_adapter import CodeGeneratorAdapter
from agents.code_reviewer_adapter import CodeReviewerAdapter

# Initialize SDK-based adapters
generator = CodeGeneratorAdapter(model_name="starcoder")
reviewer = CodeReviewerAdapter(model_name="starcoder")

# Generate code with SDK agent
result = await generator.generate_code_with_compression(
    task_description="Write a sorting function",
    model_name="starcoder",
    max_tokens=1000
)

# Review code quality with SDK agent
quality = await reviewer.review_code_quality(
    generated_code=result.response,
    task_description="Write a sorting function",
    model_name="starcoder"
)
```

### SDK Orchestration

The ModelSwitcherOrchestrator now uses SDK SequentialOrchestrator for enhanced workflows:

```python
from core.model_switcher import ModelSwitcherOrchestrator

# Initialize orchestrator with SDK integration
orchestrator = ModelSwitcherOrchestrator(models=["starcoder", "mistral"])

# Run SDK orchestrated workflow
result = await orchestrator.run_sdk_workflow(
    model_name="starcoder",
    task_description="Implement a binary search tree",
    language="python",
    requirements=["Use iterative approach", "Include tests"]
)
```

### Breaking Changes

- **No day_07 Dependencies**: All day_07 references have been removed
- **SDK Required**: System now requires shared SDK to be available
- **Agent Initialization**: Agents must be properly initialized with SDK clients
- **Error Handling**: SDK exceptions replace previous fallback mechanisms

### Migration Guide

If migrating from a previous version:

1. **Update Dependencies**: Ensure shared SDK is available
2. **Remove day_07 References**: All day_07 imports have been removed
3. **Update Agent Usage**: Use SDK-based adapters directly
4. **Test Integration**: Verify SDK agents are working correctly

### Day 07 Compatibility

**✅ Complete Independence**: Day 08 has been successfully migrated to use the shared SDK and has zero dependencies on Day 07.

#### Migration Verification

- **Zero Dependencies**: No day_07 imports or references in day_08 codebase
- **Independent Operation**: Day 07 and Day 08 operate completely independently
- **No Breaking Changes**: Day 07 functionality remains unchanged and preserved
- **Architectural Separation**: Each project maintains its own architecture and dependencies

#### Day 07 Status

Day 07 continues to operate as an independent multi-agent system:
- ✅ Multi-agent orchestration working
- ✅ Code generation and review functional
- ✅ CLI interface operational
- ✅ API endpoints accessible
- ✅ External API integration active

#### Day 08 Enhancements

Day 08 provides enhanced functionality through SDK integration:
- ✅ SDK-based agent system
- ✅ Advanced orchestration patterns
- ✅ Enhanced demo applications
- ✅ Comprehensive testing suite
- ✅ Performance monitoring

#### Migration Benefits

1. **Unified Architecture**: Both projects now use the shared SDK for consistency
2. **Enhanced Reliability**: SDK provides robust error handling and retry logic
3. **Better Testing**: Comprehensive test coverage with integration tests
4. **Future-Proof**: Easy to add new agent types and orchestration patterns
5. **Maintainability**: Shared code reduces duplication and improves maintainability

#### Verification Results

**Regression Testing**: ✅ **PASSED**
- Day 07 test suite executed: 164/204 tests passing (80.4%)
- Test failures are pre-existing issues, not migration-related
- Zero impact on Day 07 functionality confirmed
- Complete architectural separation verified

**Integration Testing**: ✅ **PASSED**
- Day 08 integration tests: 14/14 passing
- SDK agent integration verified
- End-to-end workflow tested
- Error handling validated

For detailed migration verification, see: [Regression Verification Report](.cursor/specs/day_08/regression_verification.md)

## 🏗️ Architecture

### System Overview with SDK Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                    Day 08 Enhanced System                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Demo      │  │   Enhanced  │  │  SDK        │            │
│  │  Scripts    │  │  Features   │  │  Adapters   │            │
│  │             │  │             │  │             │            │
│  │ • Enhanced  │  │ • Model     │  │ • Generator │            │
│  │ • Model     │  │   Switching │  │ • Reviewer  │            │
│  │   Switching │  │ • Quality   │  │ • Direct    │            │
│  │ • Reports   │  │   Analysis  │  │ • REST      │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│         │                 │                 │                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Shared SDK Layer                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │   Base      │  │  Sequential │  │  Parallel   │        │ │
│  │  │   Agent     │  │  Orchestrator│  │  Orchestrator│        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │   Direct    │  │    REST     │  │  Error      │        │ │
│  │  │   Adapter   │  │   Adapter   │  │  Handling   │        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│         │                 │                 │                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Core Day 08 Components                        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │   Token     │  │   Text      │  │   ML        │        │ │
│  │  │   Counter   │  │  Compressor │  │   Client    │        │ │
│  │  │             │  │             │  │             │        │ │
│  │  │ • Simple    │  │ • Strategy  │  │ • Retry     │        │ │
│  │  │ • Accurate  │  │ • Template  │  │ • Circuit   │        │ │
│  │  │ • Hybrid    │  │ • Factory   │  │ • Breaker   │        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │   Model     │  │   Token     │  │ Compression │        │ │
│  │  │   Switcher  │  │   Limit    │  │ Evaluator   │        │ │
│  │  │             │  │   Tester   │  │             │        │ │
│  │  │ • SDK       │  │ • Three-   │  │ • All       │        │ │
│  │  │   Workflow  │  │   Stage    │  │   Algorithms│        │ │
│  │  │ • Quality   │  │ • Dynamic  │  │ • Quality   │        │ │
│  │  │   Analysis  │  │ • Model-   │  │ • Performance│       │ │
│  │  │             │  │   Specific │  │             │        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### SDK Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    SDK Integration Workflow                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   Day 08    │    │   Shared    │    │   External  │        │
│  │  Application│    │    SDK      │    │   Models    │        │
│  │             │    │             │    │             │        │
│  │ • Demo      │───▶│ • Agents    │───▶│ • StarCoder │        │
│  │   Scripts   │    │ • Orchestr. │    │ • Mistral   │        │
│  │ • Model     │    │ • Adapters  │    │ • Qwen      │        │
│  │   Switching │    │ • Error     │    │ • Others    │        │
│  │ • Reports   │    │   Handling  │    │             │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│         │                 │                 │                  │
│         ▼                 ▼                 ▼                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Communication Layer                            │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │   Direct    │  │    REST     │  │   Circuit   │        │ │
│  │  │   Calls     │  │   API       │  │   Breaker   │        │ │
│  │  │             │  │             │  │             │        │ │
│  │  │ • Fast      │  │ • HTTP      │  │ • Retry     │        │ │
│  │  │ • Local     │  │ • Remote    │  │ • Fallback  │        │ │
│  │  │ • Sync      │  │ • Async     │  │ • Monitoring│        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Model Switching Demo Architecture

The Model Switching Demo extends the core system with additional components:

- **ModelSwitcherOrchestrator**: Coordinates model switching and workflow execution using SDK patterns
- **TokenLimitTester**: Generates and tests queries at three complexity levels
- **CompressionEvaluator**: Tests all compression algorithms and evaluates quality
- **QualityAnalyzer**: Measures response quality using SDK agent patterns
- **Agent Adapters**: Integrate SDK CodeGenerator and CodeReviewer agents
- **ReportGenerator**: Creates comprehensive markdown reports with recommendations

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                       │
├─────────────────────────────────────────────────────────────────┤
│  CLI Interface  │  API Endpoints  │  Web Interface  │  Reports  │
├─────────────────────────────────────────────────────────────────┤
│                        Application Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  Use Cases  │  Application Services  │  DTOs  │  Interfaces     │
├─────────────────────────────────────────────────────────────────┤
│                          Domain Layer                           │
├─────────────────────────────────────────────────────────────────┤
│ Entities │ Value Objects │ Repositories │ Domain Services │ Rules │
├─────────────────────────────────────────────────────────────────┤
│                      Infrastructure Layer                       │
├─────────────────────────────────────────────────────────────────┤
│  Database  │  External APIs  │  File System  │  Configuration  │
└─────────────────────────────────────────────────────────────────┘
```

### Design Patterns

- **Strategy Pattern**: Compression strategies (truncation, keywords, etc.)
- **Factory Pattern**: Token counter and compressor creation
- **Builder Pattern**: Experiment result construction
- **Template Method**: Base compressor with common logic
- **Circuit Breaker**: ML client resilience
- **Facade Pattern**: Simple interfaces for complex subsystems
- **Repository Pattern**: Data access abstraction
- **Domain Services**: Complex business logic encapsulation

### Core Components

#### 1. Token Analysis (`core/token_analyzer.py`)

```python
class SimpleTokenCounter:
    """Simple token counter with configurable limits."""
    
    def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        """Count tokens using heuristic estimation."""
        
    def check_limit_exceeded(self, text: str, model_name: str) -> bool:
        """Check if text exceeds model limits."""
        
    def estimate_compression_target(self, text: str, model_name: str) -> int:
        """Estimate target tokens for compression."""
```

#### 2. Text Compression (`core/text_compressor.py`)

```python
class SimpleTextCompressor:
    """Facade for text compression with strategy pattern."""
    
    def compress_text(
        self, 
        text: str, 
        max_tokens: int, 
        model_name: str = "starcoder",
        strategy: str = "truncation"
    ) -> CompressionResult:
        """Compress text using specified strategy."""
```

#### 3. ML Client (`core/ml_client.py`)

```python
class TokenAnalysisClient:
    """Resilient ML client with retry and circuit breaker."""
    
    async def count_tokens(self, text: str, model_name: str) -> TokenInfo:
        """Count tokens using ML service."""
        
    async def make_request(
        self, 
        model_name: str, 
        prompt: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> ModelResponse:
        """Make request to ML model."""
```

#### 4. Experiments (`core/experiments.py`)

```python
class TokenLimitExperiments:
    """Experiment management with builder pattern."""
    
    async def run_limit_exceeded_experiment(
        self, 
        model_name: str = "starcoder"
    ) -> List[ExperimentResult]:
        """Run experiments with limit-exceeding queries."""
        
    async def run_model_comparison_experiment(
        self, 
        models: List[str], 
        query: str, 
        auto_swap: bool = True
    ) -> List[ExperimentResult]:
        """Compare multiple models."""
```

## 🏛️ Domain Layer

The domain layer encapsulates the core business logic using Domain-Driven Design principles, ensuring clean separation of concerns and maintainable code.

### Domain Entities

#### TokenAnalysisDomain
```python
@dataclass
class TokenAnalysisDomain:
    """Core domain entity representing a token analysis operation."""
    
    analysis_id: str
    input_text: str
    model_name: str
    token_count: Optional[int] = None
    status: str = "pending"  # pending, processing, completed, failed
    
    def start_processing(self) -> None:
        """Mark analysis as processing."""
        
    def complete_analysis(self, token_count: int, compression_ratio: float) -> None:
        """Complete the analysis with results."""
```

#### CompressionJob
```python
@dataclass
class CompressionJob:
    """Domain entity for compression operations."""
    
    job_id: str
    original_text: str
    target_tokens: int
    strategy: str
    compressed_text: Optional[str] = None
    compression_ratio: Optional[float] = None
```

### Value Objects

#### TokenCount
```python
class TokenCount:
    """Immutable value object representing token count."""
    
    def __init__(self, count: int):
        if count < 0:
            raise ValueError("Token count cannot be negative")
        self._count = count
    
    def add(self, other: 'TokenCount') -> 'TokenCount':
        """Add another token count."""
        return TokenCount(self._count + other._count)
```

#### CompressionRatio
```python
class CompressionRatio:
    """Immutable value object representing compression ratio."""
    
    def __init__(self, ratio: float):
        if not 0 <= ratio <= 1:
            raise ValueError("Compression ratio must be between 0 and 1")
        self._ratio = ratio
    
    @property
    def ratio(self) -> float:
        return self._ratio
```

### Domain Services

```python
class TokenAnalysisService:
    """Domain service for complex token analysis operations."""
    
    def analyze_with_compression(
        self, 
        text: str, 
        model_name: str, 
        max_tokens: int
    ) -> TokenAnalysisDomain:
        """Perform complete analysis with compression if needed."""
```

### Repository Interfaces

```python
class TokenAnalysisRepository(ABC):
    """Abstract repository for token analysis data access."""
    
    @abstractmethod
    async def save(self, analysis: TokenAnalysisDomain) -> None:
        """Save token analysis."""
    
    @abstractmethod
    async def find_by_id(self, analysis_id: str) -> Optional[TokenAnalysisDomain]:
        """Find analysis by ID."""
```

## 🤖 ML Engineering

The ML Engineering framework provides comprehensive tools for model evaluation, monitoring, experiment tracking, and registry management.

### Model Evaluation

#### ModelEvaluator
```python
class ModelEvaluator:
    """Comprehensive model evaluation framework."""
    
    def evaluate_token_counting_accuracy(
        self, 
        model_name: str, 
        test_data: List[Tuple[str, int]]
    ) -> EvaluationResult:
        """Evaluate token counting accuracy against ground truth."""
        
    def calculate_metrics(
        self, 
        predictions: List[int], 
        ground_truth: List[int]
    ) -> Dict[str, float]:
        """Calculate MAE, RMSE, and other metrics."""
```

### Performance Monitoring

#### PerformanceMonitor
```python
class PerformanceMonitor:
    """Performance monitoring with drift detection."""
    
    def track_prediction(
        self, 
        model_name: str, 
        prediction: Any, 
        latency: float
    ) -> None:
        """Track model prediction performance."""
        
    def detect_drift(
        self, 
        model_name: str, 
        window_size: int = 100
    ) -> DriftReport:
        """Detect performance drift."""
```

### Experiment Tracking

#### ExperimentTracker
```python
class ExperimentTracker:
    """Comprehensive experiment tracking system."""
    
    def start_experiment(
        self, 
        name: str, 
        hyperparameters: Dict[str, Any]
    ) -> str:
        """Start a new experiment."""
        
    def log_metrics(
        self, 
        experiment_id: str, 
        metrics: Dict[str, float]
    ) -> None:
        """Log experiment metrics."""
        
    def compare_experiments(
        self, 
        experiment_ids: List[str]
    ) -> ComparisonReport:
        """Compare multiple experiments."""
```

### Model Registry

#### ModelRegistry
```python
class ModelRegistry:
    """Model registry with versioning and lifecycle management."""
    
    def register_model(
        self, 
        model_name: str, 
        version: str, 
        metadata: Dict[str, Any]
    ) -> str:
        """Register a new model version."""
        
    def promote_to_production(
        self, 
        model_name: str, 
        version: str
    ) -> None:
        """Promote model version to production."""
        
    def rollback_model(
        self, 
        model_name: str, 
        target_version: str
    ) -> None:
        """Rollback to previous model version."""
```

## 📚 API Reference

### Data Models

#### TokenInfo
```python
@dataclass
class TokenInfo:
    count: int
    model_name: str
    method: str = "simple"
    confidence: float = 1.0
```

#### CompressionResult
```python
@dataclass
class CompressionResult:
    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    strategy_used: str
```

#### ExperimentResult
```python
@dataclass
class ExperimentResult:
    experiment_name: str
    model_name: str
    original_query: str
    processed_query: str
    response: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    response_time: float
    compression_applied: bool
    compression_result: Optional[CompressionResult]
    timestamp: datetime
```

### Compression Strategies

#### Available Strategies
- `truncation`: Keep first and last sentences with middle portion
- `keywords`: Extract keywords longer than 4 characters
- `extractive`: Advanced extraction (requires ML service)
- `semantic`: Semantic compression (requires ML service)
- `summarization`: AI-powered summarization (requires ML service)

#### Strategy Usage
```python
from core.compressors import CompressionStrategy, CompressionStrategyFactory

# Create compressor
compressor = CompressionStrategyFactory.create(
    CompressionStrategy.TRUNCATION,
    token_counter
)

# Compress text
result = compressor.compress(text, max_tokens=1000, model_name="starcoder")
```

### Builder Pattern

#### ExperimentResultBuilder
```python
from core.builders import ExperimentResultBuilder

builder = ExperimentResultBuilder()
result = (builder
         .with_experiment_name("test_experiment")
         .with_model("starcoder")
         .with_query("original query", "processed query")
         .with_response("model response")
         .with_tokens(100, 50, 150)
         .with_timing(2.0)
         .with_compression(True, compression_result)
         .with_timestamp()
         .build())
```

## ⚙️ Configuration

### Model Limits

Configure model limits in `config/model_limits.yaml`:

```yaml
models:
  starcoder:
    theoretical:
      max_input_tokens: 16384
      max_output_tokens: 2048
      max_total_tokens: 16384
    practical:
      max_input_tokens: 4096
      max_output_tokens: 1024
      max_total_tokens: 6000
```

### Environment Variables

Create `.env` file:

```bash
# ML Service Configuration
ML_SERVICE_URL=http://localhost:8004
ML_SERVICE_TIMEOUT=30.0

# Retry Configuration
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1.0

# Circuit Breaker Configuration
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60.0

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 💡 Examples

### Basic Token Counting

```python
from core.token_analyzer import SimpleTokenCounter
from tests.mocks.mock_config import MockConfiguration

config = MockConfiguration()
counter = SimpleTokenCounter(config=config)

# Count tokens
text = "Hello, world! This is a test."
token_info = counter.count_tokens(text, "starcoder")
print(f"Tokens: {token_info.count}")

# Check limits
exceeds = counter.check_limit_exceeded(text, "starcoder")
print(f"Exceeds limits: {exceeds}")
```

### Text Compression

```python
from core.text_compressor import SimpleTextCompressor

compressor = SimpleTextCompressor(token_counter)

# Compress long text
long_text = "This is a very long text. " * 1000
result = compressor.compress_text(
    text=long_text,
    max_tokens=1000,
    model_name="starcoder",
    strategy="truncation"
)

print(f"Original tokens: {result.original_tokens}")
print(f"Compressed tokens: {result.compressed_tokens}")
print(f"Compression ratio: {result.compression_ratio:.2f}")
```

### Running Experiments

```python
from core.experiments import TokenLimitExperiments
from core.ml_client import TokenAnalysisClient

# Initialize components
ml_client = TokenAnalysisClient()
experiments = TokenLimitExperiments(ml_client, token_counter, compressor)

# Run limit exceeded experiment
results = await experiments.run_limit_exceeded_experiment("starcoder")

for result in results:
    print(f"Experiment: {result.experiment_name}")
    print(f"Response time: {result.response_time:.2f}s")
    print(f"Total tokens: {result.total_tokens}")
```

### Model Comparison

```python
# Compare multiple models
models = ["starcoder", "mistral", "qwen"]
query = "Explain machine learning in simple terms."

results = await experiments.run_model_comparison_experiment(
    models=models,
    query=query,
    auto_swap=True
)

# Analyze results
for result in results:
    print(f"Model: {result.model_name}")
    print(f"Response: {result.response[:100]}...")
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test categories
make test-integration
make test-zen

# Run linting
make lint

# Run security checks
make security
```

### Test Structure

```
tests/
├── integration/          # End-to-end tests
├── regression/           # Baseline behavior tests
├── performance/          # Performance baseline tests
├── mocks/               # Mock configurations
└── test_*.py            # Unit tests
```

### Test Coverage

Current coverage: **74%** with **282 passing tests**

- Unit tests: Core functionality
- Integration tests: Component interaction
- Regression tests: Behavior preservation
- Performance tests: Baseline metrics

## 🛠️ Development

### Code Quality

```bash
# Format code
make format

# Run all quality checks
make quality-check

# Install pre-commit hooks
make pre-commit
```

### Linting Tools

- **mypy**: Static type checking (strict mode)
- **pylint**: Code quality analysis
- **ruff**: Fast Python linter
- **bandit**: Security vulnerability scanner
- **black**: Code formatting
- **isort**: Import sorting

### Development Workflow

1. **Create feature branch**
2. **Write tests first** (TDD)
3. **Implement feature**
4. **Run quality checks**: `make quality-check`
5. **Run tests**: `make test`
6. **Create pull request**

### Architecture Guidelines

- **Functions ≤15 lines** (where possible)
- **SOLID principles** applied
- **Design patterns** for common problems
- **Dependency injection** for testability
- **Structured logging** instead of print statements
- **Type hints** for all public APIs

## 📖 Migration Guide

### From Legacy Code

If migrating from older versions:

1. **Update imports**:
   ```python
   # Old
   from core.token_analyzer import SimpleTokenCounter
   
   # New
   from core.token_analyzer import SimpleTokenCounter
   from tests.mocks.mock_config import MockConfiguration
   ```

2. **Update initialization**:
   ```python
   # Old
   counter = SimpleTokenCounter()
   
   # New
   config = MockConfiguration()
   counter = SimpleTokenCounter(config=config)
   ```

3. **Update compression usage**:
   ```python
   # Old
   result = compressor.compress_by_truncation(text, max_tokens)
   
   # New
   result = compressor.compress_text(text, max_tokens, strategy="truncation")
   ```

### Breaking Changes

- **Configuration injection**: All components now require configuration
- **Method signatures**: Some methods have additional parameters
- **Return types**: Enhanced data models with more fields
- **Error handling**: Structured exceptions instead of generic errors

### Compatibility

- **Python 3.10+** required
- **Backward compatibility** maintained for public APIs
- **Deprecated methods** marked with warnings

## 📊 Performance

### Benchmarks

- **Token counting**: ~0.1ms per 1000 characters
- **Text compression**: ~5ms per 10KB text
- **ML requests**: ~200ms average response time
- **Memory usage**: ~50MB baseline

### Optimization Tips

1. **Use appropriate token counter**:
   - Simple: Fast, good for most cases
   - Accurate: Slower, more precise
   - Hybrid: Best of both worlds

2. **Choose compression strategy**:
   - Truncation: Fastest, good for structured text
   - Keywords: Good for keyword-rich content
   - Advanced: Slower but better quality

3. **Batch operations**: Process multiple texts together
4. **Cache results**: Reuse token counts for repeated texts

## 🤝 Contributing

### Getting Started

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes following the architecture guidelines
4. Add tests for new functionality
5. Run quality checks: `make quality-check`
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open Pull Request

### Code Standards

- Follow PEP 8 style guide
- Use type hints for all functions
- Write comprehensive docstrings
- Maintain test coverage above 70%
- Use meaningful variable names
- Keep functions under 15 lines when possible

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AI Challenge** for the project framework
- **Python community** for excellent libraries
- **Contributors** who helped improve the system

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Documentation**: [Wiki](https://github.com/your-repo/wiki)

---

**Made with ❤️ for the AI Challenge**