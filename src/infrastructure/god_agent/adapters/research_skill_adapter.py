"""Research skill adapter for God Agent."""

import uuid
from typing import Any, Dict

from src.application.rag.use_case import CompareRagAnswersUseCase
from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.skill_result import SkillResult, SkillResultStatus
from src.domain.god_agent.interfaces.skill_adapter import ISkillAdapter
from src.domain.god_agent.value_objects.skill import SkillType
from src.domain.rag import Query
from src.infrastructure.logging import get_logger

logger = get_logger("research_skill_adapter")


class ResearchSkillAdapter:
    """Research skill adapter.

    Purpose:
        Wraps CompareRagAnswersUseCase to provide research skill
        interface for God Agent with citations.

    Attributes:
        compare_rag_answers_use_case: Use case for RAG comparison.

    Example:
        >>> adapter = ResearchSkillAdapter(compare_rag_answers_use_case)
        >>> result = await adapter.execute(
        ...     {"query": "What is MapReduce?"},
        ...     memory_snapshot
        ... )
    """

    def __init__(self, compare_rag_answers_use_case: CompareRagAnswersUseCase) -> None:
        """Initialize research skill adapter.

        Args:
            compare_rag_answers_use_case: Use case for RAG comparison.
        """
        self.compare_rag_answers_use_case = compare_rag_answers_use_case
        logger.info("ResearchSkillAdapter initialized")

    async def execute(
        self, input_data: Dict[str, Any], memory_snapshot: MemorySnapshot
    ) -> SkillResult:
        """Execute research skill.

        Purpose:
            Execute RAG-based research using CompareRagAnswersUseCase
            and convert result to SkillResult with citations.

        Args:
            input_data: Input dictionary with 'query', optional 'user_id'.
            memory_snapshot: Memory snapshot for context (not used directly,
                but available for future enhancements).

        Returns:
            SkillResult with answer, citations, and metadata.

        Example:
            >>> result = await adapter.execute(
            ...     {"query": "What is MapReduce?"},
            ...     memory_snapshot
            ... )
            >>> result.status
            <SkillResultStatus.SUCCESS: 'success'>
        """
        try:
            # Extract input data
            query_text = input_data.get("query", "")
            user_id = input_data.get("user_id", memory_snapshot.user_id)

            if not query_text:
                return SkillResult(
                    result_id=str(uuid.uuid4()),
                    status=SkillResultStatus.FAILURE,
                    error="Missing 'query' in input_data",
                )

            # Create Query
            query = Query(
                id=str(uuid.uuid4()),
                question=query_text,
                language="en",
            )

            # Execute use case
            comparison_result = await self.compare_rag_answers_use_case.execute(query)

            # Extract citations from chunks
            citations = [
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "source_path": chunk.source_path,
                    "similarity_score": chunk.similarity_score,
                    "text_preview": chunk.text[:200]
                    if len(chunk.text) > 200
                    else chunk.text,
                }
                for chunk in comparison_result.chunks_used
            ]

            # Convert to SkillResult
            return SkillResult(
                result_id=str(uuid.uuid4()),
                status=SkillResultStatus.SUCCESS,
                output={
                    "answer": comparison_result.with_rag.text,
                    "citations": citations,
                    "chunks_used": len(comparison_result.chunks_used),
                    "model": comparison_result.with_rag.model,
                    "latency_ms": comparison_result.with_rag.latency_ms,
                },
                metadata={
                    "skill_type": SkillType.RESEARCH.value,
                    "query_id": query.id,
                    "timestamp": comparison_result.timestamp,
                },
            )

        except Exception as e:
            logger.error(
                "Research skill execution failed",
                extra={"error": str(e), "input_data": input_data},
                exc_info=True,
            )
            return SkillResult(
                result_id=str(uuid.uuid4()),
                status=SkillResultStatus.FAILURE,
                error=f"Research skill error: {str(e)}",
            )

    def get_skill_id(self) -> str:
        """Get skill identifier.

        Purpose:
            Return unique identifier for research skill.

        Returns:
            Skill type as string ('research').

        Example:
            >>> adapter.get_skill_id()
            'research'
        """
        return SkillType.RESEARCH.value
