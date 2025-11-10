"""Unit tests for repo cleanup tooling."""

import json
from pathlib import Path
from typing import List

from tools.repo_cleanup import (
    MoveAction,
    MoveInstruction,
    build_actions,
    execute_actions,
    load_move_plan,
)


def _write_json_plan(target: Path, instructions: List[dict]) -> Path:
    """Helper to write a JSON move plan under the temporary directory."""
    target.write_text(json.dumps({"moves": instructions}), encoding="utf-8")
    return target


def test_load_move_plan_from_json(tmp_path: Path) -> None:
    """Validate that JSON plans are loaded into MoveInstruction objects."""
    plan_path = _write_json_plan(
        tmp_path / "plan.json",
        [{"source": "docs/README.md", "destination": "docs/guides/en/README.md"}],
    )

    instructions = load_move_plan(plan_path)

    assert instructions == [
        MoveInstruction(
            source=Path("docs/README.md"),
            destination=Path("docs/guides/en/README.md"),
        )
    ]


def test_build_actions_resolves_absolute_paths(tmp_path: Path) -> None:
    """Ensure build_actions resolves relative instructions under the base directory."""
    (tmp_path / "docs").mkdir()
    source_file = tmp_path / "docs" / "README.md"
    source_file.write_text("content", encoding="utf-8")

    plan_path = _write_json_plan(
        tmp_path / "plan.json",
        [{"source": "docs/README.md", "destination": "docs/archive/README.md"}],
    )

    instructions = load_move_plan(plan_path)
    actions = build_actions(tmp_path, instructions)

    assert actions == [
        MoveAction(
            instruction=instructions[0],
            source_path=tmp_path / "docs" / "README.md",
            destination_path=tmp_path / "docs" / "archive" / "README.md",
        )
    ]


def test_execute_actions_moves_files(tmp_path: Path) -> None:
    """Verify that execute_actions performs filesystem moves and creates parents."""
    source_dir = tmp_path / "docs"
    source_dir.mkdir()
    source_file = source_dir / "README.md"
    source_file.write_text("hello", encoding="utf-8")

    plan_path = _write_json_plan(
        tmp_path / "plan.json",
        [{"source": "docs/README.md", "destination": "docs/guides/en/README.md"}],
    )

    instructions = load_move_plan(plan_path)
    actions = build_actions(tmp_path, instructions)

    execute_actions(actions, dry_run=False, use_git=False)

    destination_file = tmp_path / "docs" / "guides" / "en" / "README.md"
    assert destination_file.read_text(encoding="utf-8") == "hello"
    assert not source_file.exists()


def test_execute_actions_dry_run_keeps_files(tmp_path: Path) -> None:
    """Dry run must not mutate the filesystem."""
    source_dir = tmp_path / "docs"
    source_dir.mkdir()
    source_file = source_dir / "README.md"
    source_file.write_text("hello", encoding="utf-8")

    plan_path = _write_json_plan(
        tmp_path / "plan.json",
        [{"source": "docs/README.md", "destination": "docs/guides/en/README.md"}],
    )

    instructions = load_move_plan(plan_path)
    actions = build_actions(tmp_path, instructions)

    execute_actions(actions, dry_run=True, use_git=False)

    destination_file = tmp_path / "docs" / "guides" / "en" / "README.md"
    assert not destination_file.exists()
    assert source_file.exists()
