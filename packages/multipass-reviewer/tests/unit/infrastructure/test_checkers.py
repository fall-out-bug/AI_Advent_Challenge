"""Unit tests for core modular checkers."""

from __future__ import annotations

import pytest
from multipass_reviewer.infrastructure.checkers.base import CheckerResult
from multipass_reviewer.infrastructure.checkers.haiku import HaikuChecker
from multipass_reviewer.infrastructure.checkers.linter import LinterChecker
from multipass_reviewer.infrastructure.checkers.python_style import PythonStyleChecker
from multipass_reviewer.infrastructure.checkers.type_checker import TypeChecker


@pytest.mark.asyncio
async def test_python_style_checker_flags_missing_docstring() -> None:
    checker = PythonStyleChecker()
    code = {
        "handlers.py": "def foo():\n    return 1\n",
    }

    result = await checker.run(code)

    assert isinstance(result, CheckerResult)
    assert result.checker == "python_style"
    assert result.issues[0]["rule"] == "missing_docstring"


@pytest.mark.asyncio
async def test_linter_checker_detects_trailing_whitespace() -> None:
    checker = LinterChecker()
    code = {
        "service.py": "value = 1  \n",
    }

    result = await checker.run(code)

    assert result.issues
    assert any(issue["rule"] == "trailing_whitespace" for issue in result.issues)


@pytest.mark.asyncio
async def test_type_checker_requires_annotations() -> None:
    checker = TypeChecker()
    code = {
        "module.py": "def foo(x):\n    return x\n",
    }

    result = await checker.run(code)

    assert result.severity == "major"
    assert result.issues[0]["rule"] == "missing_type_hints"


@pytest.mark.asyncio
async def test_haiku_checker_generates_poem() -> None:
    checker = HaikuChecker()
    result = await checker.run({"summary": "Architecture stable"})

    assert result.checker == "haiku"
    assert "haiku" in result.metadata
    poem = result.metadata["haiku"]
    assert len(poem.split("\n")) == 3
