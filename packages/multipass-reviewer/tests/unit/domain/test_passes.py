"""Unit tests for architecture, component, and synthesis passes."""

from __future__ import annotations

import pytest
from multipass_reviewer.application.config import ReviewConfig
from multipass_reviewer.domain.passes.architecture_pass import ArchitectureReviewPass
from multipass_reviewer.domain.passes.base_pass import BaseReviewPass
from multipass_reviewer.domain.passes.component_pass import ComponentDeepDivePass
from multipass_reviewer.domain.passes.synthesis_pass import SynthesisPass


class DummyLogger:
    def __init__(self) -> None:
        self.entries: list[tuple[str, str]] = []

    def log_review_pass(
        self, pass_name: str, event: str, data: object | None = None
    ) -> None:
        self.entries.append((pass_name, event))

    def log_work_step(self, *args: object, **kwargs: object) -> None:
        return None

    def log_model_interaction(self, *args: object, **kwargs: object) -> None:
        return None

    def log_reasoning(self, *args: object, **kwargs: object) -> None:
        return None


@pytest.mark.asyncio
async def test_architecture_pass_generates_findings() -> None:
    logger = DummyLogger()
    config = ReviewConfig(language_checkers=["python"])
    review_pass = ArchitectureReviewPass(
        config=config, review_logger=logger  # type: ignore[arg-type]
    )

    result = await review_pass.run({"main.py": "print('hi')"})

    assert result.pass_name == "architecture"
    assert result.status == "completed"
    assert isinstance(result.findings, list)
    assert logger.entries and logger.entries[0][0] == "architecture"


@pytest.mark.asyncio
async def test_component_pass_handles_multiple_files() -> None:
    logger = DummyLogger()
    config = ReviewConfig(language_checkers=["python"])
    review_pass = ComponentDeepDivePass(
        config=config, review_logger=logger  # type: ignore[arg-type]
    )

    result = await review_pass.run(
        {
            "services/user.py": "class User: ...",
            "services/order.py": "class Order: ...",
        }
    )

    assert result.pass_name == "component"
    assert result.status == "completed"
    assert result.metadata.get("files_scanned") == 2


@pytest.mark.asyncio
async def test_synthesis_pass_combines_inputs() -> None:
    logger = DummyLogger()
    config = ReviewConfig(language_checkers=["python"], enable_haiku=True)
    review_pass = SynthesisPass(
        config=config, review_logger=logger  # type: ignore[arg-type]
    )

    result = await review_pass.run({"main.py": "print('hello')"})

    assert result.pass_name == "synthesis"
    assert result.status == "completed"
    assert "summary" in (result.summary or "")
    if config.enable_haiku:
        assert result.metadata.get("haiku")


def test_build_failure_result_records_error() -> None:
    logger = DummyLogger()

    class ExplodingPass(BaseReviewPass):
        def __init__(self) -> None:
            super().__init__("explode", logger)  # type: ignore[arg-type]

        async def run(self, archive):  # pragma: no cover - helper stub
            self._start_timer_if_needed()
            raise RuntimeError("boom")

    review_pass = ExplodingPass()
    review_pass._start_timer_if_needed()
    failure = review_pass.build_failure_result(RuntimeError("boom"))

    assert failure.pass_name == "explode"
    assert failure.status == "failed"
    assert failure.error == "boom"
    assert failure.metadata.get("status") == "error"
    assert logger.entries and logger.entries[-1][1] == "error"
