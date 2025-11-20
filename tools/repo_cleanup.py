"""Repository cleanup orchestration utilities."""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

try:  # pragma: no cover - optional dependency
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


LOGGER = logging.getLogger("repo_cleanup")


@dataclass(frozen=True)
class MoveInstruction:
    """Relative move specification for a repository asset.

    Purpose:
        Represent a single instruction to relocate a file or directory within
        the repository.

    Args:
        source: Source path relative to the repository root.
        destination: Destination path relative to the repository root.

    Returns:
        None.

    Raises:
        ValueError: When either path is absolute.

    Example:
        >>> MoveInstruction(Path("docs/README.md"), Path("docs/archive/README.md"))
        MoveInstruction(...)
    """

    source: Path
    destination: Path

    def __post_init__(self) -> None:
        """Validate that paths are relative."""
        if self.source.is_absolute():
            msg = f"Source path must be relative: {self.source}"
            raise ValueError(msg)
        if self.destination.is_absolute():
            msg = f"Destination path must be relative: {self.destination}"
            raise ValueError(msg)


@dataclass(frozen=True)
class MoveAction:
    """Concrete file system action derived from a move instruction.

    Purpose:
        Bind a move instruction to absolute source and destination paths under a
        given repository root.

    Args:
        instruction: The original relative move instruction.
        source_path: Absolute path to the resource that will be moved.
        destination_path: Absolute path where the resource will be relocated.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> MoveAction(  # doctest: +SKIP
        ...     instruction=MoveInstruction(Path('a'), Path('b')),
        ...     source_path=Path('/repo/a'),
        ...     destination_path=Path('/repo/b'),
        ... )
        MoveAction(...)
    """

    instruction: MoveInstruction
    source_path: Path
    destination_path: Path


def load_move_plan(config_path: Path) -> List[MoveInstruction]:
    """Load move instructions from a JSON or YAML configuration file.

    Purpose:
        Parse the user-provided configuration describing repository move
        operations into an internal representation.

    Args:
        config_path: Absolute or relative path to the config file.

    Returns:
        A list of move instructions preserving the order defined in the config.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: When the config format is unsupported or malformed.

    Example:
        >>> from pathlib import Path
        >>> plan = load_move_plan(Path("plan.json"))  # doctest: +SKIP
    """

    if not config_path.exists():
        msg = f"Plan file not found: {config_path}"
        raise FileNotFoundError(msg)

    suffix = config_path.suffix.lower()
    data: dict
    if suffix == ".json":
        data = json.loads(config_path.read_text(encoding="utf-8"))
    elif suffix in (".yaml", ".yml"):
        if yaml is None:  # pragma: no cover
            msg = "PyYAML is required to load YAML plans."
            raise ValueError(msg)
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    else:
        msg = f"Unsupported plan format: {config_path}"
        raise ValueError(msg)

    moves = data.get("moves")
    if not isinstance(moves, list):
        msg = "Plan must contain a 'moves' list."
        raise ValueError(msg)

    instructions: List[MoveInstruction] = []
    for raw_move in moves:
        if not isinstance(raw_move, dict):
            msg = f"Invalid move entry: {raw_move}"
            raise ValueError(msg)
        source_value = raw_move.get("source")
        destination_value = raw_move.get("destination")
        if not source_value or not destination_value:
            msg = f"Move entry must define source and destination: {raw_move}"
            raise ValueError(msg)
        instructions.append(
            MoveInstruction(
                source=Path(source_value),
                destination=Path(destination_value),
            )
        )
    return instructions


def build_actions(
    base_dir: Path, instructions: Sequence[MoveInstruction]
) -> List[MoveAction]:
    """Resolve move instructions into executable file system actions.

    Purpose:
        Combine the repository root with relative instruction paths and sanity
        check that each source exists.

    Args:
        base_dir: Repository root against which paths are resolved.
        instructions: Ordered collection of move instructions.

    Returns:
        A list of concrete actions containing absolute source and destination
        paths.

    Raises:
        FileNotFoundError: When a referenced source path does not exist.

    Example:
        >>> base = Path.cwd()
        >>> actions = build_actions(base, [])  # doctest: +ELLIPSIS
        []
    """

    actions: List[MoveAction] = []
    for instruction in instructions:
        source_path = (base_dir / instruction.source).resolve()
        destination_path = (base_dir / instruction.destination).resolve()
        if not source_path.exists():
            msg = f"Source path does not exist: {source_path}"
            raise FileNotFoundError(msg)
        actions.append(
            MoveAction(
                instruction=instruction,
                source_path=source_path,
                destination_path=destination_path,
            )
        )
    return actions


def execute_actions(
    actions: Iterable[MoveAction],
    dry_run: bool,
    use_git: bool,
    logger: Optional[logging.Logger] = None,
) -> List[MoveAction]:
    """Execute or log planned move actions.

    Purpose:
        Perform the actual file moves (or log them in dry-run mode) while
        ensuring parent directories exist. Supports git-aware moves to preserve
        history when required.

    Args:
        actions: Iterable of move actions generated by ``build_actions``.
        dry_run: Whether to skip changes and only log the planned operations.
        use_git: When True, use ``git mv`` instead of ``Path.rename``.
        logger: Optional logger for emitting progress information.

    Returns:
        The list of processed actions (useful for downstream reporting).

    Raises:
        subprocess.CalledProcessError: If ``git mv`` fails.

    Example:
        >>> actions = []  # doctest: +SKIP
        >>> execute_actions(actions, dry_run=True, use_git=False)  # doctest: +SKIP
        []
    """

    emitted_logger = logger or LOGGER
    processed: List[MoveAction] = []
    for action in actions:
        emitted_logger.info(
            "Move planned",
            extra={
                "source": str(action.source_path),
                "destination": str(action.destination_path),
                "dry_run": dry_run,
            },
        )
        if dry_run:
            processed.append(action)
            continue

        action.destination_path.parent.mkdir(parents=True, exist_ok=True)

        if use_git:
            subprocess.run(
                ["git", "mv", str(action.source_path), str(action.destination_path)],
                check=True,
            )
        else:
            action.source_path.rename(action.destination_path)
        processed.append(action)
    return processed


def _build_argument_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser.

    Purpose:
        Provide a reusable parser for the command line interface so integration
        tests can instantiate it without executing actions.

    Args:
        None.

    Returns:
        Configured ``ArgumentParser`` instance.

    Raises:
        None.

    Example:
        >>> parser = _build_argument_parser()
        >>> isinstance(parser, argparse.ArgumentParser)
        True
    """

    parser = argparse.ArgumentParser(
        description="Execute scripted repository cleanup moves.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to JSON or YAML plan describing repo moves.",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("."),
        help="Optional repository root; defaults to current working directory.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Apply changes (omit for dry-run reporting).",
    )
    parser.add_argument(
        "--use-git",
        action="store_true",
        help="Use git mv to preserve history when running in a repository.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level for cleanup output.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point for the repo cleanup tool.

    Purpose:
        Parse CLI arguments, execute the configured moves, and return an exit
        status suitable for automation.

    Args:
        argv: Optional argument list; defaults to ``sys.argv`` when omitted.

    Returns:
        Process exit code (0 on success, 1 on failure).

    Raises:
        None. Exceptions are logged and converted into non-zero exit codes.

    Example:
        >>> main(["--config", "plan.json"])  # doctest: +SKIP
        0
    """

    parser = _build_argument_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level))
    try:
        instructions = load_move_plan(args.config)
        actions = build_actions(args.base_dir, instructions)
        execute_actions(actions, dry_run=not args.execute, use_git=args.use_git)
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Cleanup failed", exc_info=exc)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI invocation
    raise SystemExit(main())
