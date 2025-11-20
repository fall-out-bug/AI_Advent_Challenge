"""Day 21 demo launcher for RAG++ personas and configuration overrides."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Iterable, Sequence

from scripts.rag import day_20_demo as base_demo
from src.domain.rag import FilterConfig, Query


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run RAG++ demo conversation with configurable persona and filters."
    )
    parser.add_argument(
        "--persona",
        choices=list(base_demo.PERSONAS.keys()),
        default="1",
        help="Persona identifier (matches day_20_demo).",
    )
    parser.add_argument(
        "--filter",
        dest="filter_enabled",
        action="store_true",
        help="Force-enable threshold filtering (overrides config).",
    )
    parser.add_argument(
        "--no-filter",
        dest="filter_enabled",
        action="store_false",
        help="Disable filtering entirely.",
    )
    parser.set_defaults(filter_enabled=None)
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Override score threshold (0.0-1.0). Applies only when filtering is active.",
    )
    parser.add_argument(
        "--reranker",
        choices=["off", "llm", "cross_encoder"],
        default=None,
        help="Override reranker strategy. 'cross_encoder' falls back to 'off'.",
    )
    parser.add_argument(
        "--questions",
        type=Path,
        default=None,
        help="Optional path to a UTF-8 text file with one question per line.",
    )
    return parser.parse_args()


_DEFAULT_QUESTIONS: Tuple[str, ...] = (
    "Какие слои предусмотрены Clean Architecture и что в них запрещено?",
    "Как готовится отчёт об эпиках?",
    "Какие MCP‑инструменты поддержаны?",
    "Что такое MapReduce и как устроены map/shuffle/reduce?",
    "Когда RAG не улучшит ответ и почему?",
    "Какой workflow генерации отчёта об эпике в Stage 21?",
    "Какой функционал покрывает backoffice CLI для RAG++?",
    "Как настроить фильтрацию чанков в FilterConfig?",
    "Какие метрики Prometheus собираются для RAG++?",
    "Как выполняется план отката (rollback) для RAG++?",
)


def _load_questions(path: Path | None) -> Sequence[str]:
    if path is None:
        return _DEFAULT_QUESTIONS
    raw = path.read_text(encoding="utf-8").splitlines()
    return tuple(line.strip() for line in raw if line.strip())


def _override_filter_config(
    base_config: FilterConfig,
    *,
    filter_enabled: bool | None,
    threshold_override: float | None,
    reranker_override: str | None,
) -> FilterConfig:
    # Clamp threshold into range when provided.
    if threshold_override is not None and not 0.0 <= threshold_override <= 1.0:
        raise ValueError("threshold must be between 0.0 and 1.0.")

    top_k = base_config.top_k
    threshold = (
        threshold_override
        if threshold_override is not None
        else base_config.score_threshold
    )

    if filter_enabled is False:
        return FilterConfig(score_threshold=0.0, top_k=top_k)

    strategy = reranker_override or base_config.reranker_strategy
    enabled = (
        (reranker_override != "off")
        if reranker_override is not None
        else base_config.reranker_enabled
    )

    if filter_enabled is True and threshold == 0.0:
        threshold = base_config.score_threshold or 0.3

    if not filter_enabled and not base_config.reranker_enabled:
        # ensure we don't accidentally enable reranker without filter flag.
        enabled = False
        strategy = "off"

    if not filter_enabled and threshold_override is None:
        threshold = base_config.score_threshold

    if filter_enabled is None and strategy != "off":
        filter_enabled = True

    if filter_enabled is False:
        enabled = False
        strategy = "off"
        threshold = 0.0

    if strategy == "cross_encoder":
        # Cross-encoder support deferred; fall back gracefully.
        strategy = "off"
        enabled = False

    if enabled:
        return FilterConfig.with_reranking(
            score_threshold=threshold,
            top_k=top_k,
            strategy=strategy,
        )

    return FilterConfig(
        score_threshold=threshold,
        top_k=top_k,
        reranker_enabled=False,
        reranker_strategy="off",
    )


async def _run_demo(
    persona_key: str,
    persona: base_demo.PersonaConfig,
    use_case,
    questions: Iterable[str],
    filter_config: FilterConfig,
) -> None:
    print("=== RAG++ Demo ===")
    print(f"Persona: {persona.title}")
    print(
        f"FilterConfig: threshold={filter_config.score_threshold:.2f}, "
        f"top_k={filter_config.top_k}, reranker_enabled={filter_config.reranker_enabled}, "
        f"strategy={filter_config.reranker_strategy}"
    )
    print()

    for idx, question in enumerate(questions, start=1):
        query = Query(id=f"demo_{idx}", question=question)
        result = await use_case.execute(query, filter_config=filter_config)

        base_demo.typing_print(f"Вопрос {idx}: {question}")
        base_demo.typing_print("\nБез RAG:\n", delay=0.01)
        base_demo.typing_print(result.without_rag.text, delay=0.015)
        base_demo.typing_print("\nС RAG++:\n", delay=0.01)
        base_demo.typing_print(result.with_rag.text, delay=0.015)

        print()
        print(base_demo.format_chunks(result.chunks_used))
        print("\n" + "=" * 70 + "\n")


def main() -> None:
    args = _parse_arguments()
    questions = _load_questions(args.questions)
    persona = base_demo.PERSONAS[args.persona]
    use_case, base_config = base_demo.build_use_case(persona)
    # We already received use_case, but we will rebuild in async run; only keep filter config.
    filter_config = _override_filter_config(
        base_config,
        filter_enabled=args.filter_enabled,
        threshold_override=args.threshold,
        reranker_override=args.reranker,
    )

    asyncio.run(
        _run_demo(
            persona_key=args.persona,
            persona=persona,
            use_case=use_case,
            questions=questions,
            filter_config=filter_config,
        )
    )


if __name__ == "__main__":
    main()
