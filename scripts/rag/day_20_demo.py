"""Interactive console demo for Stage 20 (RAG vs non-RAG)."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Sequence

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from src.application.rag import (
    CompareRagAnswersUseCase,
    PromptAssembler,
    RetrievalService,
)
from src.domain.embedding_index import EmbeddingGateway
from src.domain.rag import Query, RetrievedChunk
from src.infrastructure.config.settings import get_settings
from src.infrastructure.embedding_index.gateways.local_embedding_gateway import (
    LocalEmbeddingGateway,
)
from src.infrastructure.embedding_index.repositories.mongo_document_repository import (
    MongoChunkRepository,
    MongoDocumentRepository,
)
from src.infrastructure.embeddings import LocalEmbeddingClient
from src.infrastructure.rag import LLMServiceAdapter, VectorSearchAdapter

QUESTIONS: Sequence[str] = (
    "Какие слои предусмотрены Clean Architecture и что в них запрещено?",
    "Как готовится отчёт об эпиках?",
    "Какие MCP‑инструменты поддержаны?",
    "Что такое MapReduce и как устроены map/shuffle/reduce?",
    "Когда RAG не улучшит ответ и почему?",
)


@dataclass(frozen=True)
class PersonaConfig:
    title: str
    prompt: str | None
    temperature: float | None = None


PERSONAS: Dict[str, PersonaConfig] = {
    "1": PersonaConfig(
        title="Обычный бот",
        prompt=None,
        temperature=None,
    ),
    "2": PersonaConfig(
        title="Ехидный дедушка",
        prompt=(
            "Ты ехидный ворчливый дед, отвечай с прибаутками, подколами и"
            " народной мудростью, но всё же давай полезные советы."
        ),
        temperature=0.9,
    ),
}


def typing_print(text: str, delay: float = 0.02) -> None:
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


class PersonaPromptAssembler(PromptAssembler):
    def __init__(self, persona_prompt: str | None, *, max_context_tokens: int) -> None:
        super().__init__(max_context_tokens=max_context_tokens)
        self._persona_prompt = persona_prompt

    def _prepend_persona(self, prompt: str) -> str:
        if not self._persona_prompt:
            return prompt
        return f"{self._persona_prompt}\n\n{prompt}"

    def build_non_rag_prompt(self, question: str) -> str:  # type: ignore[override]
        base = super().build_non_rag_prompt(question)
        return self._prepend_persona(base)

    def build_rag_prompt(  # type: ignore[override]
        self,
        question: str,
        chunks: Sequence[RetrievedChunk],
    ) -> str:
        base = super().build_rag_prompt(question, chunks)
        return self._prepend_persona(base)


def build_use_case(persona: PersonaConfig) -> CompareRagAnswersUseCase:
    settings = get_settings()

    mongo_client = MongoClient(settings.mongodb_url)
    database = mongo_client[settings.embedding_mongo_database]
    chunk_collection = database[settings.embedding_mongo_chunks_collection]
    document_collection = database[settings.embedding_mongo_documents_collection]
    chunk_repository = MongoChunkRepository(chunk_collection, ensure_indexes=False)
    document_repository = MongoDocumentRepository(document_collection)

    embedding_client = LocalEmbeddingClient(
        base_url=settings.embedding_api_url or "http://127.0.0.1:8000",
        model=settings.embedding_model,
        timeout=settings.embedding_api_timeout_seconds,
    )
    embedding_gateway: EmbeddingGateway = LocalEmbeddingGateway(
        client=embedding_client,
        fallback_dimension=settings.embedding_vector_dimension,
    )

    vector_search = VectorSearchAdapter(
        chunk_repository=chunk_repository,
        document_repository=document_repository,
        fallback_index_path=Path("var/indices/embedding_index_v1.pkl"),
    )
    retrieval_service = RetrievalService(vector_search=vector_search)

    prompt_assembler = PersonaPromptAssembler(
        persona_prompt=persona.prompt,
        max_context_tokens=settings.rag_max_context_tokens,
    )

    llm_service = LLMServiceAdapter(
        base_url=settings.llm_url or "http://127.0.0.1:8000",
        model=settings.llm_model,
        timeout_seconds=settings.review_llm_timeout,
    )

    temperature = persona.temperature or settings.llm_temperature

    return CompareRagAnswersUseCase(
        embedding_gateway=embedding_gateway,
        retrieval_service=retrieval_service,
        prompt_assembler=prompt_assembler,
        llm_service=llm_service,
        top_k=settings.rag_top_k,
        score_threshold=settings.rag_score_threshold,
        max_tokens=settings.llm_max_tokens,
        temperature=temperature,
    )


def choose_persona() -> PersonaConfig:
    print("Выберите личность:")
    for key, persona in PERSONAS.items():
        print(f"  {key}. {persona.title}")
    try:
        choice = input("Введите номер (1-2): ").strip()
    except EOFError:
        print("(ввода не получено — выбран вариант по умолчанию)")
        choice = "1"
    persona = PERSONAS.get(choice, PERSONAS["1"])
    print(f"\n▶ Выбрана личность: {persona.title}\n")
    return persona


def format_chunks(chunks: Sequence[RetrievedChunk]) -> str:
    if not chunks:
        return "  (фрагменты не использовались)"
    lines = ["  Использованные фрагменты:"]
    for chunk in chunks:
        metadata = chunk.metadata or {}
        raw_path = (
            chunk.source_path or metadata.get("source_path") or metadata.get("path")
        )
        path = raw_path or f"doc:{chunk.document_id}"
        stage = metadata.get("stage")
        stage_suffix = f", stage={stage}" if stage else ""
        lines.append(f"  - {path}{stage_suffix} (score={chunk.similarity_score:.2f})")
    return "\n".join(lines)


def main() -> int:
    persona = choose_persona()

    try:
        use_case = build_use_case(persona)
    except PyMongoError as error:
        print(f"Ошибка подключения к MongoDB: {error}")
        return 1
    except Exception as error:  # noqa: BLE001
        print(f"Не удалось инициировать use case: {error}")
        return 1

    print("=== Диалог RAG vs Non-RAG ===\n")

    for idx, question in enumerate(QUESTIONS, start=1):
        query = Query(id=f"demo_{idx}", question=question)
        result = use_case.execute(query)

        typing_print(f"Вопрос {idx}: {question}")
        time.sleep(0.5)

        typing_print("\nБез RAG:\n", delay=0.01)
        typing_print(result.without_rag.text, delay=0.015)
        time.sleep(0.3)

        typing_print("\nС RAG:\n", delay=0.01)
        typing_print(result.with_rag.text, delay=0.015)
        time.sleep(0.3)

        print()
        print(format_chunks(result.chunks_used))
        print("\n" + "=" * 70 + "\n")
        time.sleep(0.5)

    print("Демо завершено. Спасибо! ✨")
    return 0


if __name__ == "__main__":
    sys.exit(main())
