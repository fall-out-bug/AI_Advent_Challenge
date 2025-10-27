#!/usr/bin/env python3
"""
Domain Layer Usage Examples

This script demonstrates how to use the domain layer components including
entities, value objects, domain services, and repositories.
"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Optional

from core.text_compressor import SimpleTextCompressor

# Core imports
from core.token_analyzer import SimpleTokenCounter

# Domain imports
from domain.entities.token_analysis_entities import (
    CompressionJob,
    ExperimentSession,
    TokenAnalysisDomain,
)
from domain.repositories.token_analysis_repositories import TokenAnalysisRepository
from domain.services.token_analysis_services import TokenAnalysisService
from domain.value_objects.token_analysis_values import (
    CompressionRatio,
    ModelSpecification,
    ProcessingTime,
    QualityScore,
    TokenCount,
)
from tests.mocks.mock_config import MockConfiguration


class MockTokenAnalysisRepository(TokenAnalysisRepository):
    """Mock repository implementation for examples."""

    def __init__(self):
        self.analyses: dict = {}

    async def save(self, analysis: TokenAnalysisDomain) -> None:
        """Save token analysis."""
        self.analyses[analysis.analysis_id] = analysis
        print(f"Saved analysis: {analysis.analysis_id}")

    async def find_by_id(self, analysis_id: str) -> Optional[TokenAnalysisDomain]:
        """Find analysis by ID."""
        return self.analyses.get(analysis_id)

    async def find_by_model(
        self, model_name: str, limit: int = 100
    ) -> List[TokenAnalysisDomain]:
        """Find analyses by model name."""
        return [
            analysis
            for analysis in self.analyses.values()
            if analysis.model_name == model_name
        ][:limit]

    async def find_recent(
        self, hours: int = 24, limit: int = 100
    ) -> List[TokenAnalysisDomain]:
        """Find recent analyses."""
        cutoff = datetime.now().timestamp() - (hours * 3600)
        return [
            analysis
            for analysis in self.analyses.values()
            if analysis.created_at.timestamp() > cutoff
        ][:limit]


def demonstrate_value_objects():
    """Demonstrate value object usage."""
    print("=== Value Objects Demo ===")

    # TokenCount value object
    print("\n1. TokenCount Value Object:")
    token_count = TokenCount(150)
    print(f"Token count: {token_count.count}")

    # Operations
    total_tokens = token_count.add(TokenCount(50))
    print(f"After adding 50: {total_tokens.count}")

    remaining_tokens = token_count.subtract(TokenCount(25))
    print(f"After subtracting 25: {remaining_tokens.count}")

    scaled_tokens = token_count.multiply(1.5)
    print(f"After scaling by 1.5: {scaled_tokens.count}")

    # CompressionRatio value object
    print("\n2. CompressionRatio Value Object:")
    ratio = CompressionRatio(0.7)
    print(f"Compression ratio: {ratio.ratio}")
    print(f"Is effective (threshold 0.5): {ratio.is_effective(0.5)}")
    print(f"Compression percentage: {ratio.compression_percentage():.1f}%")

    # ModelSpecification value object
    print("\n3. ModelSpecification Value Object:")
    model_spec = ModelSpecification("starcoder", "2.0", "huggingface")
    print(f"Model name: {model_spec.name}")
    print(f"Version: {model_spec.version}")
    print(f"Provider: {model_spec.provider}")
    print(f"Full name: {model_spec.full_name()}")

    # ProcessingTime value object
    print("\n4. ProcessingTime Value Object:")
    processing_time = ProcessingTime(0.15)
    print(f"Processing time: {processing_time.seconds}s")
    print(f"Processing time: {processing_time.milliseconds}ms")
    print(f"Is fast (threshold 1.0s): {processing_time.is_fast(1.0)}")

    # QualityScore value object
    print("\n5. QualityScore Value Object:")
    quality = QualityScore(0.85)
    print(f"Quality score: {quality.score}")
    print(f"Quality level: {quality.quality_level()}")
    print(f"Is high quality (threshold 0.8): {quality.is_high_quality(0.8)}")


def demonstrate_domain_entities():
    """Demonstrate domain entity usage."""
    print("\n=== Domain Entities Demo ===")

    # TokenAnalysisDomain entity
    print("\n1. TokenAnalysisDomain Entity:")
    analysis = TokenAnalysisDomain(
        analysis_id=str(uuid.uuid4()),
        input_text="This is a sample text for token analysis",
        model_name="starcoder",
        model_version="2.0",
    )

    print(f"Analysis ID: {analysis.analysis_id}")
    print(f"Initial status: {analysis.status}")
    print(f"Is completed: {analysis.is_completed()}")

    # State transitions
    analysis.start_processing()
    print(f"After starting: {analysis.status}")

    analysis.complete_analysis(
        token_count=8,
        compression_ratio=0.8,
        processing_time=0.15,
        confidence_score=0.95,
    )
    print(f"After completion: {analysis.status}")
    print(f"Token count: {analysis.token_count}")
    print(f"Compression ratio: {analysis.compression_ratio}")
    print(f"Is completed: {analysis.is_completed()}")

    # CompressionJob entity
    print("\n2. CompressionJob Entity:")
    job = CompressionJob(
        job_id=str(uuid.uuid4()),
        original_text="This is a very long text that needs compression for token analysis",
        target_tokens=5,
        strategy="truncation",
        model_name="starcoder",
    )

    print(f"Job ID: {job.job_id}")
    print(f"Initial status: {job.status}")

    job.start_compression()
    print(f"After starting compression: {job.status}")

    job.complete_compression(
        compressed_text="Long text compressed",
        compression_ratio=0.6,
        processing_time=0.25,
    )
    print(f"After completion: {job.status}")
    print(f"Compression ratio: {job.compression_ratio}")

    # ExperimentSession entity
    print("\n3. ExperimentSession Entity:")
    session = ExperimentSession(
        session_id=str(uuid.uuid4()),
        experiment_name="token_analysis_comparison",
        model_name="starcoder",
        configuration={"strategy": "hybrid", "max_tokens": 1000, "temperature": 0.7},
    )

    print(f"Session ID: {session.session_id}")
    print(f"Experiment name: {session.experiment_name}")
    print(f"Configuration: {session.configuration}")
    print(f"Status: {session.status}")

    # Add results (mock)
    from models.data_models import ExperimentResult

    result = ExperimentResult(
        experiment_name="test",
        model_name="starcoder",
        original_query="test query",
        processed_query="test query",
        response="test response",
        input_tokens=10,
        output_tokens=5,
        total_tokens=15,
        response_time=0.5,
        compression_applied=False,
        compression_result=None,
        timestamp=datetime.now(),
    )

    session.add_result(result)
    print(f"Results count: {len(session.results)}")

    best_result = session.get_best_result()
    if best_result:
        print(f"Best result total tokens: {best_result.total_tokens}")


async def demonstrate_domain_services():
    """Demonstrate domain service usage."""
    print("\n=== Domain Services Demo ===")

    # Initialize dependencies
    config = MockConfiguration()
    token_counter = SimpleTokenCounter(config=config)
    compressor = SimpleTextCompressor(token_counter)
    repository = MockTokenAnalysisRepository()

    # Initialize domain service
    service = TokenAnalysisService(
        token_counter=token_counter, compressor=compressor, repository=repository
    )

    print("\n1. Token Analysis Service:")

    # Analyze with compression
    model_spec = ModelSpecification("starcoder", "2.0", "huggingface")
    text = "This is a sample text for analysis with compression if needed"

    analysis = await service.analyze_with_compression(
        text=text,
        model_spec=model_spec,
        max_tokens=5,  # Low limit to trigger compression
    )

    print(f"Analysis ID: {analysis.analysis_id}")
    print(f"Status: {analysis.status}")
    print(f"Token count: {analysis.token_count}")
    print(f"Compression ratio: {analysis.compression_ratio}")

    # Batch analysis
    print("\n2. Batch Analysis:")
    texts = [
        "Short text",
        "This is a longer text for analysis",
        "Another text for batch processing",
    ]

    analyses = await service.batch_analyze(texts=texts, model_spec=model_spec)

    print(f"Processed {len(analyses)} texts")
    for i, analysis in enumerate(analyses):
        print(f"  Text {i+1}: {analysis.token_count} tokens, status: {analysis.status}")


async def demonstrate_repository_pattern():
    """Demonstrate repository pattern usage."""
    print("\n=== Repository Pattern Demo ===")

    repository = MockTokenAnalysisRepository()

    # Create and save analyses
    analyses = []
    for i in range(3):
        analysis = TokenAnalysisDomain(
            analysis_id=str(uuid.uuid4()),
            input_text=f"Sample text {i+1}",
            model_name="starcoder",
            model_version="2.0",
        )
        analysis.start_processing()
        analysis.complete_analysis(
            token_count=5 + i,
            compression_ratio=0.8,
            processing_time=0.1 + i * 0.05,
            confidence_score=0.9,
        )

        await repository.save(analysis)
        analyses.append(analysis)

    print(f"Saved {len(analyses)} analyses")

    # Find by ID
    first_analysis = await repository.find_by_id(analyses[0].analysis_id)
    if first_analysis:
        print(f"Found analysis by ID: {first_analysis.analysis_id}")

    # Find by model
    starcoder_analyses = await repository.find_by_model("starcoder")
    print(f"Found {len(starcoder_analyses)} analyses for starcoder model")

    # Find recent
    recent_analyses = await repository.find_recent(hours=1)
    print(f"Found {len(recent_analyses)} recent analyses")


def demonstrate_domain_events():
    """Demonstrate domain events (conceptual)."""
    print("\n=== Domain Events Demo ===")

    print("Domain events would be used to:")
    print("1. Notify other parts of the system about domain changes")
    print("2. Maintain eventual consistency across aggregates")
    print("3. Enable event sourcing for audit trails")
    print("4. Trigger side effects like notifications or logging")

    print("\nExample event flow:")
    print("1. TokenAnalysisDomain.start_processing() → AnalysisStartedEvent")
    print("2. TokenAnalysisDomain.complete_analysis() → AnalysisCompletedEvent")
    print("3. CompressionJob.complete_compression() → CompressionCompletedEvent")
    print("4. Event handlers update metrics, send notifications, etc.")


async def main():
    """Main demonstration function."""
    print("Domain Layer Usage Examples")
    print("=" * 50)

    # Demonstrate value objects
    demonstrate_value_objects()

    # Demonstrate domain entities
    demonstrate_domain_entities()

    # Demonstrate domain services
    await demonstrate_domain_services()

    # Demonstrate repository pattern
    await demonstrate_repository_pattern()

    # Demonstrate domain events (conceptual)
    demonstrate_domain_events()

    print("\n" + "=" * 50)
    print("Domain Layer Demo Complete!")
    print("\nKey Benefits Demonstrated:")
    print("✓ Immutable value objects with validation")
    print("✓ Rich domain entities with business logic")
    print("✓ Domain services for complex operations")
    print("✓ Repository pattern for data access")
    print("✓ Clean separation of concerns")
    print("✓ Type safety and error handling")


if __name__ == "__main__":
    asyncio.run(main())
