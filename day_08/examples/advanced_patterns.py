#!/usr/bin/env python3
"""
Advanced Patterns Examples

This script demonstrates advanced design patterns and architectural concepts
including SOLID principles, Clean Architecture, and production-ready patterns.
"""

import asyncio
import random
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar

from core.text_compressor import SimpleTextCompressor

# Core imports
from core.token_analyzer import SimpleTokenCounter
from tests.mocks.mock_config import MockConfiguration

# Advanced Design Patterns Examples


class CompressionStrategy(Enum):
    """Compression strategy enumeration."""

    TRUNCATION = "truncation"
    KEYWORDS = "keywords"
    SEMANTIC = "semantic"
    SUMMARIZATION = "summarization"


@dataclass
class CompressionContext:
    """Context for compression operations."""

    text: str
    max_tokens: int
    model_name: str
    strategy: CompressionStrategy
    metadata: Dict[str, Any] = field(default_factory=dict)


class CompressionStrategyInterface(Protocol):
    """Protocol for compression strategies."""

    def compress(self, context: CompressionContext) -> str:
        """Compress text according to strategy."""
        ...


class TruncationStrategy:
    """Truncation compression strategy."""

    def compress(self, context: CompressionContext) -> str:
        """Compress by truncating text."""
        words = context.text.split()
        if len(words) <= context.max_tokens:
            return context.text

        truncated_words = words[: context.max_tokens]
        return " ".join(truncated_words) + "..."


class KeywordsStrategy:
    """Keywords extraction compression strategy."""

    def compress(self, context: CompressionContext) -> str:
        """Compress by extracting keywords."""
        words = context.text.split()
        if len(words) <= context.max_tokens:
            return context.text

        # Simple keyword extraction (in practice, use NLP libraries)
        keywords = [word for word in words if len(word) > 4][: context.max_tokens]
        return " ".join(keywords)


class SemanticStrategy:
    """Semantic compression strategy."""

    def compress(self, context: CompressionContext) -> str:
        """Compress using semantic understanding."""
        # Mock semantic compression
        sentences = context.text.split(". ")
        if len(sentences) <= context.max_tokens // 5:  # Rough estimation
            return context.text

        # Keep first and last sentences, summarize middle
        if len(sentences) > 2:
            compressed = sentences[0] + ". [Summary of content]. " + sentences[-1]
        else:
            compressed = sentences[0]

        return compressed


class CompressionStrategyFactory:
    """Factory for creating compression strategies."""

    _strategies = {
        CompressionStrategy.TRUNCATION: TruncationStrategy,
        CompressionStrategy.KEYWORDS: KeywordsStrategy,
        CompressionStrategy.SEMANTIC: SemanticStrategy,
    }

    @classmethod
    def create_strategy(
        cls, strategy: CompressionStrategy
    ) -> CompressionStrategyInterface:
        """Create compression strategy instance."""
        if strategy not in cls._strategies:
            raise ValueError(f"Unknown strategy: {strategy}")

        return cls._strategies[strategy]()


def demonstrate_strategy_pattern():
    """Demonstrate Strategy pattern."""
    print("=== Strategy Pattern Demo ===")

    text = "This is a very long text that needs compression for token analysis. " * 3
    context = CompressionContext(
        text=text,
        max_tokens=10,
        model_name="starcoder",
        strategy=CompressionStrategy.TRUNCATION,
    )

    print(f"Original text length: {len(text.split())} words")
    print(f"Target tokens: {context.max_tokens}")

    # Test different strategies
    strategies = [
        CompressionStrategy.TRUNCATION,
        CompressionStrategy.KEYWORDS,
        CompressionStrategy.SEMANTIC,
    ]

    for strategy in strategies:
        context.strategy = strategy
        compressor = CompressionStrategyFactory.create_strategy(strategy)
        compressed = compressor.compress(context)

        print(f"\n{strategy.value.title()} Strategy:")
        print(f"  Compressed: {compressed}")
        print(f"  Length: {len(compressed.split())} words")


# Builder Pattern Example


@dataclass
class ExperimentConfiguration:
    """Experiment configuration."""

    name: str
    model_name: str
    max_tokens: int
    strategies: List[CompressionStrategy]
    iterations: int
    timeout: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExperimentConfigurationBuilder:
    """Builder for experiment configuration."""

    def __init__(self):
        self._config = ExperimentConfiguration(
            name="",
            model_name="starcoder",
            max_tokens=1000,
            strategies=[],
            iterations=1,
            timeout=30.0,
        )

    def with_name(self, name: str) -> "ExperimentConfigurationBuilder":
        """Set experiment name."""
        self._config.name = name
        return self

    def with_model(self, model_name: str) -> "ExperimentConfigurationBuilder":
        """Set model name."""
        self._config.model_name = model_name
        return self

    def with_max_tokens(self, max_tokens: int) -> "ExperimentConfigurationBuilder":
        """Set maximum tokens."""
        self._config.max_tokens = max_tokens
        return self

    def with_strategies(
        self, strategies: List[CompressionStrategy]
    ) -> "ExperimentConfigurationBuilder":
        """Set compression strategies."""
        self._config.strategies = strategies
        return self

    def with_iterations(self, iterations: int) -> "ExperimentConfigurationBuilder":
        """Set number of iterations."""
        self._config.iterations = iterations
        return self

    def with_timeout(self, timeout: float) -> "ExperimentConfigurationBuilder":
        """Set timeout."""
        self._config.timeout = timeout
        return self

    def with_metadata(
        self, metadata: Dict[str, Any]
    ) -> "ExperimentConfigurationBuilder":
        """Set metadata."""
        self._config.metadata.update(metadata)
        return self

    def build(self) -> ExperimentConfiguration:
        """Build the configuration."""
        if not self._config.name:
            raise ValueError("Experiment name is required")

        if not self._config.strategies:
            raise ValueError("At least one strategy is required")

        return self._config


def demonstrate_builder_pattern():
    """Demonstrate Builder pattern."""
    print("\n=== Builder Pattern Demo ===")

    # Build experiment configuration
    config = (
        ExperimentConfigurationBuilder()
        .with_name("token_analysis_comparison")
        .with_model("starcoder")
        .with_max_tokens(500)
        .with_strategies(
            [
                CompressionStrategy.TRUNCATION,
                CompressionStrategy.KEYWORDS,
                CompressionStrategy.SEMANTIC,
            ]
        )
        .with_iterations(10)
        .with_timeout(60.0)
        .with_metadata(
            {
                "description": "Compare different compression strategies",
                "environment": "staging",
            }
        )
        .build()
    )

    print(f"Built configuration:")
    print(f"  Name: {config.name}")
    print(f"  Model: {config.model_name}")
    print(f"  Max tokens: {config.max_tokens}")
    print(f"  Strategies: {[s.value for s in config.strategies]}")
    print(f"  Iterations: {config.iterations}")
    print(f"  Timeout: {config.timeout}s")
    print(f"  Metadata: {config.metadata}")


# Observer Pattern Example


class Event(ABC):
    """Base event class."""

    def __init__(self, timestamp: datetime = None):
        self.timestamp = timestamp or datetime.now()
        self.event_id = str(uuid.uuid4())


class AnalysisStartedEvent(Event):
    """Event fired when analysis starts."""

    def __init__(self, analysis_id: str, model_name: str):
        super().__init__()
        self.analysis_id = analysis_id
        self.model_name = model_name


class AnalysisCompletedEvent(Event):
    """Event fired when analysis completes."""

    def __init__(self, analysis_id: str, token_count: int, processing_time: float):
        super().__init__()
        self.analysis_id = analysis_id
        self.token_count = token_count
        self.processing_time = processing_time


class EventObserver(ABC):
    """Observer interface for events."""

    @abstractmethod
    def handle_event(self, event: Event) -> None:
        """Handle an event."""
        pass


class MetricsObserver(EventObserver):
    """Observer that tracks metrics."""

    def __init__(self):
        self.metrics: Dict[str, List[Any]] = {
            "analysis_count": [],
            "processing_times": [],
            "token_counts": [],
        }

    def handle_event(self, event: Event) -> None:
        """Handle events for metrics tracking."""
        if isinstance(event, AnalysisStartedEvent):
            self.metrics["analysis_count"].append(event.timestamp)
        elif isinstance(event, AnalysisCompletedEvent):
            self.metrics["processing_times"].append(event.processing_time)
            self.metrics["token_counts"].append(event.token_count)

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return {
            "total_analyses": len(self.metrics["analysis_count"]),
            "avg_processing_time": sum(self.metrics["processing_times"])
            / len(self.metrics["processing_times"])
            if self.metrics["processing_times"]
            else 0,
            "avg_token_count": sum(self.metrics["token_counts"])
            / len(self.metrics["token_counts"])
            if self.metrics["token_counts"]
            else 0,
        }


class LoggingObserver(EventObserver):
    """Observer that logs events."""

    def handle_event(self, event: Event) -> None:
        """Log events."""
        if isinstance(event, AnalysisStartedEvent):
            print(
                f"[LOG] Analysis {event.analysis_id} started for model {event.model_name}"
            )
        elif isinstance(event, AnalysisCompletedEvent):
            print(
                f"[LOG] Analysis {event.analysis_id} completed: {event.token_count} tokens in {event.processing_time:.3f}s"
            )


class EventBus:
    """Event bus for managing observers and events."""

    def __init__(self):
        self.observers: List[EventObserver] = []

    def subscribe(self, observer: EventObserver) -> None:
        """Subscribe observer to events."""
        self.observers.append(observer)

    def unsubscribe(self, observer: EventObserver) -> None:
        """Unsubscribe observer from events."""
        if observer in self.observers:
            self.observers.remove(observer)

    def publish(self, event: Event) -> None:
        """Publish event to all observers."""
        for observer in self.observers:
            observer.handle_event(event)


def demonstrate_observer_pattern():
    """Demonstrate Observer pattern."""
    print("\n=== Observer Pattern Demo ===")

    # Create event bus and observers
    event_bus = EventBus()
    metrics_observer = MetricsObserver()
    logging_observer = LoggingObserver()

    # Subscribe observers
    event_bus.subscribe(metrics_observer)
    event_bus.subscribe(logging_observer)

    # Simulate analysis events
    analysis_id = str(uuid.uuid4())

    # Start analysis
    start_event = AnalysisStartedEvent(analysis_id, "starcoder")
    event_bus.publish(start_event)

    # Simulate processing time
    time.sleep(0.1)

    # Complete analysis
    complete_event = AnalysisCompletedEvent(analysis_id, 150, 0.1)
    event_bus.publish(complete_event)

    # Get metrics summary
    summary = metrics_observer.get_summary()
    print(f"\nMetrics Summary:")
    print(f"  Total analyses: {summary['total_analyses']}")
    print(f"  Average processing time: {summary['avg_processing_time']:.3f}s")
    print(f"  Average token count: {summary['avg_token_count']:.0f}")


# Command Pattern Example


class Command(ABC):
    """Base command interface."""

    @abstractmethod
    def execute(self) -> Any:
        """Execute the command."""
        pass

    @abstractmethod
    def undo(self) -> Any:
        """Undo the command."""
        pass


class TokenAnalysisCommand(Command):
    """Command for token analysis."""

    def __init__(self, text: str, model_name: str, token_counter: SimpleTokenCounter):
        self.text = text
        self.model_name = model_name
        self.token_counter = token_counter
        self.result = None

    def execute(self) -> Any:
        """Execute token analysis."""
        print(f"Executing token analysis for: {self.text[:50]}...")
        self.result = self.token_counter.count_tokens(self.text, self.model_name)
        return self.result

    def undo(self) -> Any:
        """Undo token analysis (not applicable for read operations)."""
        print("Cannot undo token analysis (read operation)")
        return None


class CompressionCommand(Command):
    """Command for text compression."""

    def __init__(
        self,
        text: str,
        max_tokens: int,
        strategy: CompressionStrategy,
        compressor: SimpleTextCompressor,
    ):
        self.original_text = text
        self.max_tokens = max_tokens
        self.strategy = strategy
        self.compressor = compressor
        self.result = None

    def execute(self) -> Any:
        """Execute compression."""
        print(f"Executing compression with {self.strategy.value} strategy")
        self.result = self.compressor.compress_text(
            text=self.original_text,
            max_tokens=self.max_tokens,
            model_name="starcoder",
            strategy=self.strategy.value,
        )
        return self.result

    def undo(self) -> Any:
        """Undo compression (return original text)."""
        print("Undoing compression - returning original text")
        return self.original_text


class CommandInvoker:
    """Invoker for commands."""

    def __init__(self):
        self.history: List[Command] = []

    def execute_command(self, command: Command) -> Any:
        """Execute a command and add to history."""
        result = command.execute()
        self.history.append(command)
        return result

    def undo_last_command(self) -> Any:
        """Undo the last command."""
        if not self.history:
            print("No commands to undo")
            return None

        last_command = self.history.pop()
        return last_command.undo()


def demonstrate_command_pattern():
    """Demonstrate Command pattern."""
    print("\n=== Command Pattern Demo ===")

    # Initialize components
    config = MockConfiguration()
    token_counter = SimpleTokenCounter(config=config)
    compressor = SimpleTextCompressor(token_counter)
    invoker = CommandInvoker()

    # Create and execute commands
    text = "This is a sample text for command pattern demonstration"

    # Token analysis command
    analysis_command = TokenAnalysisCommand(text, "starcoder", token_counter)
    result = invoker.execute_command(analysis_command)
    print(f"Analysis result: {result.count} tokens")

    # Compression command
    compression_command = CompressionCommand(
        text, 5, CompressionStrategy.TRUNCATION, compressor
    )
    result = invoker.execute_command(compression_command)
    print(f"Compression result: {result.compressed_tokens} tokens")

    # Undo operations
    print("\nUndoing operations:")
    invoker.undo_last_command()  # Undo compression
    invoker.undo_last_command()  # Undo analysis


# Generic Repository Pattern

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Generic repository interface."""

    @abstractmethod
    async def save(self, entity: T) -> None:
        """Save entity."""
        pass

    @abstractmethod
    async def find_by_id(self, entity_id: str) -> Optional[T]:
        """Find entity by ID."""
        pass

    @abstractmethod
    async def find_all(self, limit: int = 100) -> List[T]:
        """Find all entities."""
        pass

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete entity by ID."""
        pass


@dataclass
class AnalysisEntity:
    """Analysis entity for repository example."""

    id: str
    text: str
    token_count: int
    timestamp: datetime


class InMemoryAnalysisRepository(Repository[AnalysisEntity]):
    """In-memory implementation of analysis repository."""

    def __init__(self):
        self.entities: Dict[str, AnalysisEntity] = {}

    async def save(self, entity: AnalysisEntity) -> None:
        """Save analysis entity."""
        self.entities[entity.id] = entity
        print(f"Saved analysis entity: {entity.id}")

    async def find_by_id(self, entity_id: str) -> Optional[AnalysisEntity]:
        """Find analysis entity by ID."""
        return self.entities.get(entity_id)

    async def find_all(self, limit: int = 100) -> List[AnalysisEntity]:
        """Find all analysis entities."""
        return list(self.entities.values())[:limit]

    async def delete(self, entity_id: str) -> bool:
        """Delete analysis entity by ID."""
        if entity_id in self.entities:
            del self.entities[entity_id]
            print(f"Deleted analysis entity: {entity_id}")
            return True
        return False


async def demonstrate_repository_pattern():
    """Demonstrate Repository pattern."""
    print("\n=== Repository Pattern Demo ===")

    repository = InMemoryAnalysisRepository()

    # Create and save entities
    entities = []
    for i in range(3):
        entity = AnalysisEntity(
            id=str(uuid.uuid4()),
            text=f"Sample text {i+1}",
            token_count=5 + i,
            timestamp=datetime.now(),
        )
        await repository.save(entity)
        entities.append(entity)

    # Find by ID
    found_entity = await repository.find_by_id(entities[0].id)
    if found_entity:
        print(f"Found entity: {found_entity.text} ({found_entity.token_count} tokens)")

    # Find all
    all_entities = await repository.find_all()
    print(f"Total entities: {len(all_entities)}")

    # Delete entity
    deleted = await repository.delete(entities[0].id)
    print(f"Entity deleted: {deleted}")

    # Verify deletion
    remaining_entities = await repository.find_all()
    print(f"Remaining entities: {len(remaining_entities)}")


# Circuit Breaker Pattern


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service is back


class CircuitBreaker:
    """Circuit breaker implementation."""

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED

    def call(self, func, *args, **kwargs):
        """Call function through circuit breaker."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit."""
        if self.last_failure_time is None:
            return True

        return time.time() - self.last_failure_time >= self.timeout

    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


def demonstrate_circuit_breaker():
    """Demonstrate Circuit Breaker pattern."""
    print("\n=== Circuit Breaker Pattern Demo ===")

    circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=5.0)

    def unreliable_service():
        """Simulate unreliable service."""
        if random.random() < 0.7:  # 70% failure rate
            raise Exception("Service unavailable")
        return "Service response"

    # Test circuit breaker
    for i in range(10):
        try:
            result = circuit_breaker.call(unreliable_service)
            print(f"Call {i+1}: SUCCESS - {result}")
        except Exception as e:
            print(f"Call {i+1}: FAILED - {e}")
            print(f"Circuit state: {circuit_breaker.state.value}")

        time.sleep(0.5)


async def main():
    """Main demonstration function."""
    print("Advanced Patterns Examples")
    print("=" * 50)

    # Demonstrate Strategy pattern
    demonstrate_strategy_pattern()

    # Demonstrate Builder pattern
    demonstrate_builder_pattern()

    # Demonstrate Observer pattern
    demonstrate_observer_pattern()

    # Demonstrate Command pattern
    demonstrate_command_pattern()

    # Demonstrate Repository pattern
    await demonstrate_repository_pattern()

    # Demonstrate Circuit Breaker pattern
    demonstrate_circuit_breaker()

    print("\n" + "=" * 50)
    print("Advanced Patterns Demo Complete!")
    print("\nPatterns Demonstrated:")
    print("✓ Strategy Pattern - Flexible algorithm selection")
    print("✓ Builder Pattern - Complex object construction")
    print("✓ Observer Pattern - Event-driven architecture")
    print("✓ Command Pattern - Encapsulated operations")
    print("✓ Repository Pattern - Data access abstraction")
    print("✓ Circuit Breaker Pattern - Fault tolerance")
    print("\nBenefits:")
    print("✓ Improved code maintainability")
    print("✓ Enhanced flexibility and extensibility")
    print("✓ Better separation of concerns")
    print("✓ Increased testability")
    print("✓ Production-ready patterns")


if __name__ == "__main__":
    asyncio.run(main())
