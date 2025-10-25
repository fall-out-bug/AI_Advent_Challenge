# Domain Guide

## Overview

This guide explains the Domain-Driven Design (DDD) principles and patterns implemented in the Enhanced Token Analysis System. The domain layer encapsulates the core business logic and ensures clean separation of concerns.

## Table of Contents

- [Domain-Driven Design Principles](#domain-driven-design-principles)
- [Domain Entities](#domain-entities)
- [Value Objects](#value-objects)
- [Domain Services](#domain-services)
- [Repository Pattern](#repository-pattern)
- [Aggregates](#aggregates)
- [Domain Events](#domain-events)
- [Best Practices](#best-practices)

## Domain-Driven Design Principles

### Core Concepts

#### 1. Ubiquitous Language

The domain layer uses a common vocabulary that reflects the business domain:

- **Token Analysis**: The process of analyzing text to determine token counts
- **Compression Job**: A task to compress text while maintaining quality
- **Experiment Session**: A collection of related experiments
- **Model Specification**: Details about a specific model version
- **Quality Score**: Assessment of analysis or compression quality

#### 2. Bounded Context

The token analysis domain is clearly bounded and isolated from other domains:

```python
# Domain boundaries
domain/
├── entities/           # Core business objects
├── value_objects/     # Immutable domain concepts
├── repositories/      # Data access interfaces
├── services/         # Domain business logic
└── events/          # Domain events
```

#### 3. Domain Model

The domain model represents the core business concepts and their relationships:

```python
# Domain model relationships
TokenAnalysisDomain ──┐
                      ├── TokenCount (value object)
                      ├── ModelSpecification (value object)
                      └── CompressionRatio (value object)

CompressionJob ───────┐
                      ├── TokenCount (value object)
                      ├── CompressionRatio (value object)
                      └── ProcessingTime (value object)

ExperimentSession ────┐
                      ├── ExperimentResult (entity)
                      └── ModelSpecification (value object)
```

## Domain Entities

### Overview

Domain entities are objects with identity and lifecycle. They encapsulate business logic and maintain invariants.

### TokenAnalysisDomain

The core entity representing a token analysis operation:

```python
from domain.entities.token_analysis_entities import TokenAnalysisDomain

# Create analysis
analysis = TokenAnalysisDomain(
    analysis_id="analysis_001",
    input_text="Sample text for analysis",
    model_name="starcoder",
    model_version="1.0"
)

# Business logic methods
analysis.start_processing()
analysis.complete_analysis(
    token_count=150,
    compression_ratio=0.7,
    processing_time=0.15,
    confidence_score=0.95
)

# State queries
if analysis.is_completed():
    print(f"Analysis completed with {analysis.token_count} tokens")
```

#### Entity Responsibilities

1. **Identity Management**: Maintain unique identity throughout lifecycle
2. **State Management**: Track entity state and transitions
3. **Business Rules**: Enforce domain invariants and business rules
4. **Behavior**: Provide methods for domain operations

#### Entity Lifecycle

```python
# Entity lifecycle states
class AnalysisStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# State transitions
analysis.start_processing()      # pending → processing
analysis.complete_analysis(...)  # processing → completed
analysis.fail_analysis("error")  # processing → failed
```

### CompressionJob

Entity for managing compression operations:

```python
from domain.entities.token_analysis_entities import CompressionJob

# Create compression job
job = CompressionJob(
    job_id="compression_001",
    original_text="Very long text that needs compression...",
    target_tokens=1000,
    strategy="truncation",
    model_name="starcoder"
)

# Execute compression
job.start_compression()
job.complete_compression(
    compressed_text="Compressed text...",
    compression_ratio=0.6,
    processing_time=0.25
)
```

### ExperimentSession

Entity for managing experiment sessions:

```python
from domain.entities.token_analysis_entities import ExperimentSession

# Create experiment session
session = ExperimentSession(
    session_id="session_001",
    experiment_name="token_analysis_comparison",
    model_name="starcoder",
    configuration={
        "strategy": "hybrid",
        "max_tokens": 1000
    }
)

# Add results
result = ExperimentResult(...)
session.add_result(result)

# Get best result
best_result = session.get_best_result()
```

## Value Objects

### Overview

Value objects are immutable objects without identity. They represent concepts in the domain and encapsulate validation logic.

### TokenCount

Immutable value object representing token count:

```python
from domain.value_objects.token_analysis_values import TokenCount

# Create token count
token_count = TokenCount(150)

# Operations
total_tokens = token_count.add(TokenCount(50))  # 200
remaining_tokens = token_count.subtract(TokenCount(25))  # 125
scaled_tokens = token_count.multiply(1.5)  # 225

# Validation
try:
    invalid_count = TokenCount(-10)  # Raises ValueError
except ValueError as e:
    print(f"Invalid token count: {e}")
```

#### Value Object Benefits

1. **Immutability**: Cannot be modified after creation
2. **Validation**: Encapsulates validation logic
3. **Type Safety**: Prevents primitive obsession
4. **Equality**: Based on value, not identity
5. **Operations**: Provides domain-specific operations

### CompressionRatio

Value object for compression ratios:

```python
from domain.value_objects.token_analysis_values import CompressionRatio

# Create compression ratio
ratio = CompressionRatio(0.7)

# Check effectiveness
if ratio.is_effective(threshold=0.5):
    print("Compression is effective")

# Get percentage
percentage = ratio.compression_percentage()  # 30.0%

# Validation
try:
    invalid_ratio = CompressionRatio(1.5)  # Raises ValueError
except ValueError as e:
    print(f"Invalid compression ratio: {e}")
```

### ModelSpecification

Value object for model identification:

```python
from domain.value_objects.token_analysis_values import ModelSpecification

# Create model specification
model_spec = ModelSpecification(
    name="starcoder",
    version="2.0",
    provider="huggingface"
)

# Get full name
full_name = model_spec.full_name()  # "starcoder:2.0"

# Equality comparison
other_spec = ModelSpecification("starcoder", "2.0", "huggingface")
if model_spec == other_spec:
    print("Same model specification")
```

### ProcessingTime

Value object for processing time:

```python
from domain.value_objects.token_analysis_values import ProcessingTime

# Create processing time
processing_time = ProcessingTime(0.15)  # 150ms

# Check if fast
if processing_time.is_fast(threshold=1.0):
    print("Processing is fast")

# Get different units
seconds = processing_time.seconds  # 0.15
milliseconds = processing_time.milliseconds  # 150
```

### QualityScore

Value object for quality assessment:

```python
from domain.value_objects.token_analysis_values import QualityScore

# Create quality score
quality = QualityScore(0.85)

# Check quality level
level = quality.quality_level()  # "good"

# Check if high quality
if quality.is_high_quality(threshold=0.8):
    print("High quality result")
```

## Domain Services

### Overview

Domain services contain business logic that doesn't naturally belong to entities or value objects.

### TokenAnalysisService

Service for complex token analysis operations:

```python
from domain.services.token_analysis_services import TokenAnalysisService

# Initialize service
service = TokenAnalysisService(
    token_counter=token_counter,
    compressor=compressor,
    repository=repository
)

# Analyze with compression
analysis = await service.analyze_with_compression(
    text="Very long text...",
    model_spec=ModelSpecification("starcoder", "2.0"),
    max_tokens=1000
)

# Batch analysis
texts = ["Text 1", "Text 2", "Text 3"]
analyses = await service.batch_analyze(
    texts=texts,
    model_spec=ModelSpecification("starcoder", "2.0")
)
```

#### Service Responsibilities

1. **Complex Business Logic**: Operations that involve multiple entities
2. **Domain Calculations**: Complex calculations and algorithms
3. **Business Rules**: Rules that span multiple entities
4. **Orchestration**: Coordinate between multiple domain objects

### CompressionService

Service for compression operations:

```python
from domain.services.token_analysis_services import CompressionService

# Initialize service
compression_service = CompressionService(
    compressor=compressor,
    repository=repository
)

# Compress with quality check
compression_result = await compression_service.compress_with_quality_check(
    text="Long text...",
    target_tokens=500,
    min_quality_threshold=0.8
)
```

## Repository Pattern

### Overview

The repository pattern abstracts data access and provides a clean interface for domain operations.

### TokenAnalysisRepository

Abstract repository interface:

```python
from domain.repositories.token_analysis_repositories import TokenAnalysisRepository

class TokenAnalysisRepository(ABC):
    """Abstract repository for token analysis data access."""
    
    @abstractmethod
    async def save(self, analysis: TokenAnalysisDomain) -> None:
        """Save token analysis."""
    
    @abstractmethod
    async def find_by_id(self, analysis_id: str) -> Optional[TokenAnalysisDomain]:
        """Find analysis by ID."""
    
    @abstractmethod
    async def find_by_model(
        self, 
        model_name: str, 
        limit: int = 100
    ) -> List[TokenAnalysisDomain]:
        """Find analyses by model name."""
    
    @abstractmethod
    async def find_recent(
        self, 
        hours: int = 24, 
        limit: int = 100
    ) -> List[TokenAnalysisDomain]:
        """Find recent analyses."""
```

### Repository Implementation

```python
from infrastructure.repositories.token_analysis_repository_impl import TokenAnalysisRepositoryImpl

# Infrastructure implementation
repository = TokenAnalysisRepositoryImpl(database_connection)

# Use in domain service
service = TokenAnalysisService(
    token_counter=token_counter,
    compressor=compressor,
    repository=repository
)
```

#### Repository Benefits

1. **Abstraction**: Hides data access implementation details
2. **Testability**: Easy to mock for unit testing
3. **Flexibility**: Can change data storage without affecting domain
4. **Query Encapsulation**: Encapsulates complex queries

## Aggregates

### Overview

Aggregates are clusters of related entities and value objects that are treated as a unit for data consistency.

### TokenAnalysisAggregate

Aggregate for token analysis operations:

```python
from domain.aggregates.token_analysis_aggregate import TokenAnalysisAggregate

class TokenAnalysisAggregate:
    """Aggregate for token analysis operations."""
    
    def __init__(self, analysis: TokenAnalysisDomain):
        self.analysis = analysis
        self.compression_jobs: List[CompressionJob] = []
        self.events: List[DomainEvent] = []
    
    def add_compression_job(self, job: CompressionJob) -> None:
        """Add compression job to aggregate."""
        if self.analysis.status != "processing":
            raise ValueError("Cannot add compression job to non-processing analysis")
        
        self.compression_jobs.append(job)
        self.events.append(CompressionJobAddedEvent(job.job_id))
    
    def complete_analysis(self, results: Dict[str, Any]) -> None:
        """Complete analysis with results."""
        self.analysis.complete_analysis(
            token_count=results["token_count"],
            compression_ratio=results["compression_ratio"],
            processing_time=results["processing_time"],
            confidence_score=results["confidence_score"]
        )
        
        self.events.append(AnalysisCompletedEvent(self.analysis.analysis_id))
    
    def get_uncommitted_events(self) -> List[DomainEvent]:
        """Get uncommitted domain events."""
        return self.events.copy()
    
    def mark_events_as_committed(self) -> None:
        """Mark events as committed."""
        self.events.clear()
```

#### Aggregate Rules

1. **Consistency Boundary**: All entities in aggregate must be consistent
2. **Single Root**: One entity serves as the aggregate root
3. **Transaction Boundary**: Changes to aggregate are atomic
4. **Event Sourcing**: Track changes as domain events

## Domain Events

### Overview

Domain events represent significant business events that occur in the domain.

### Event Types

```python
from domain.events.domain_events import (
    AnalysisStartedEvent,
    AnalysisCompletedEvent,
    CompressionJobAddedEvent,
    QualityThresholdExceededEvent
)

# Event definitions
@dataclass
class AnalysisStartedEvent(DomainEvent):
    analysis_id: str
    model_name: str
    timestamp: datetime

@dataclass
class AnalysisCompletedEvent(DomainEvent):
    analysis_id: str
    token_count: int
    compression_ratio: float
    timestamp: datetime

@dataclass
class CompressionJobAddedEvent(DomainEvent):
    analysis_id: str
    job_id: str
    strategy: str
    timestamp: datetime
```

### Event Handling

```python
from domain.events.event_handler import DomainEventHandler

class TokenAnalysisEventHandler(DomainEventHandler):
    """Handle domain events for token analysis."""
    
    def handle_analysis_started(self, event: AnalysisStartedEvent) -> None:
        """Handle analysis started event."""
        logger.info(f"Analysis {event.analysis_id} started for model {event.model_name}")
        
        # Update metrics
        self.metrics_collector.increment_counter("analysis_started")
    
    def handle_analysis_completed(self, event: AnalysisCompletedEvent) -> None:
        """Handle analysis completed event."""
        logger.info(f"Analysis {event.analysis_id} completed with {event.token_count} tokens")
        
        # Update metrics
        self.metrics_collector.record_histogram("token_count", event.token_count)
        self.metrics_collector.record_histogram("compression_ratio", event.compression_ratio)
```

## Best Practices

### Entity Design

1. **Single Responsibility**: Each entity should have one clear responsibility
2. **Encapsulation**: Hide internal state and expose behavior through methods
3. **Invariants**: Enforce business rules and invariants in entity methods
4. **Immutability**: Make entities immutable where possible
5. **Identity**: Use meaningful identifiers for entities

### Value Object Design

1. **Immutability**: Value objects should be immutable
2. **Validation**: Include validation logic in constructors
3. **Equality**: Implement proper equality and hashing
4. **Operations**: Provide domain-specific operations
5. **Type Safety**: Use value objects instead of primitives

### Domain Service Design

1. **Stateless**: Domain services should be stateless
2. **Pure Functions**: Services should not have side effects
3. **Single Responsibility**: Each service should have one responsibility
4. **Dependency Injection**: Use dependency injection for dependencies
5. **Testing**: Make services easy to test in isolation

### Repository Design

1. **Interface Segregation**: Create focused repository interfaces
2. **Abstraction**: Hide implementation details from domain
3. **Query Methods**: Provide meaningful query methods
4. **Pagination**: Support pagination for large result sets
5. **Error Handling**: Handle data access errors appropriately

### Aggregate Design

1. **Consistency**: Maintain consistency within aggregate boundaries
2. **Size**: Keep aggregates small and focused
3. **Root Entity**: Have one clear aggregate root
4. **Event Sourcing**: Use events to track changes
5. **Transaction Boundaries**: Align with transaction boundaries

### Event Design

1. **Meaningful Names**: Use descriptive names for events
2. **Immutable Data**: Events should contain immutable data
3. **Timestamp**: Include timestamp in all events
4. **Versioning**: Version events for backward compatibility
5. **Handlers**: Create focused event handlers

## Testing Domain Logic

### Unit Testing Entities

```python
import pytest
from domain.entities.token_analysis_entities import TokenAnalysisDomain

def test_token_analysis_lifecycle():
    """Test token analysis entity lifecycle."""
    analysis = TokenAnalysisDomain(
        analysis_id="test_001",
        input_text="Test text",
        model_name="starcoder",
        model_version="1.0"
    )
    
    # Test initial state
    assert analysis.status == "pending"
    assert analysis.token_count is None
    
    # Test state transition
    analysis.start_processing()
    assert analysis.status == "processing"
    
    # Test completion
    analysis.complete_analysis(
        token_count=100,
        compression_ratio=0.8,
        processing_time=0.1,
        confidence_score=0.95
    )
    
    assert analysis.status == "completed"
    assert analysis.token_count == 100
    assert analysis.compression_ratio == 0.8

def test_invalid_state_transition():
    """Test invalid state transitions."""
    analysis = TokenAnalysisDomain(
        analysis_id="test_002",
        input_text="Test text",
        model_name="starcoder",
        model_version="1.0"
    )
    
    analysis.start_processing()
    
    # Should not be able to start processing again
    with pytest.raises(ValueError):
        analysis.start_processing()
```

### Unit Testing Value Objects

```python
import pytest
from domain.value_objects.token_analysis_values import TokenCount, CompressionRatio

def test_token_count_operations():
    """Test token count value object operations."""
    count1 = TokenCount(100)
    count2 = TokenCount(50)
    
    # Test addition
    total = count1.add(count2)
    assert total.count == 150
    
    # Test subtraction
    difference = count1.subtract(count2)
    assert difference.count == 50
    
    # Test multiplication
    scaled = count1.multiply(1.5)
    assert scaled.count == 150

def test_token_count_validation():
    """Test token count validation."""
    # Valid count
    valid_count = TokenCount(100)
    assert valid_count.count == 100
    
    # Invalid count
    with pytest.raises(ValueError):
        TokenCount(-10)

def test_compression_ratio_validation():
    """Test compression ratio validation."""
    # Valid ratio
    valid_ratio = CompressionRatio(0.7)
    assert valid_ratio.ratio == 0.7
    
    # Invalid ratios
    with pytest.raises(ValueError):
        CompressionRatio(-0.1)
    
    with pytest.raises(ValueError):
        CompressionRatio(1.5)
```

### Integration Testing

```python
import pytest
from domain.services.token_analysis_services import TokenAnalysisService

@pytest.mark.asyncio
async def test_token_analysis_service():
    """Test token analysis service integration."""
    # Mock dependencies
    token_counter = MockTokenCounter()
    compressor = MockCompressor()
    repository = MockRepository()
    
    # Initialize service
    service = TokenAnalysisService(
        token_counter=token_counter,
        compressor=compressor,
        repository=repository
    )
    
    # Test analysis
    analysis = await service.analyze_with_compression(
        text="Test text",
        model_spec=ModelSpecification("starcoder", "1.0"),
        max_tokens=100
    )
    
    assert analysis.is_completed()
    assert analysis.token_count > 0
    assert repository.save_called
```

## Conclusion

The domain layer provides a clean, maintainable foundation for the token analysis system. By following DDD principles and best practices, the domain layer ensures:

- **Clear Business Logic**: Domain concepts are clearly expressed
- **Maintainability**: Changes to business logic are localized
- **Testability**: Domain logic can be tested in isolation
- **Flexibility**: Domain is independent of external concerns
- **Consistency**: Business rules are enforced consistently

For additional examples and implementation details, refer to the API documentation and source code in the domain layer.
