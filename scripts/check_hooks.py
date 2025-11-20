"""Helper to rerun hooks and summarize yaml/json issues."""

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MESSAGES = ROOT / "docs/specs/epic_27/consensus/messages/inbox"
ARTIFACTS = ROOT / "docs/specs/epic_27/consensus/artifacts"


def run_precommit() -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pre-commit", "run", "--all-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def check_yaml_syntax():
    errors = []
    for path in MESSAGES.rglob("*.yaml"):
        try:
            with open(path) as fd:
                yaml.safe_load(fd)
        except yaml.YAMLError as exc:
            errors.append((path, exc))
    return errors


def check_json_syntax():
    errors = []
    for path in ARTIFACTS.glob("*.json"):
        try:
            with open(path) as fd:
                json.load(fd)
        except json.JSONDecodeError as exc:
            errors.append((path, exc))
    return errors


def main():
    print(">>> Running pre-commit hooks")
    result = run_precommit()
    print(result.stdout)
    print(result.stderr, file=sys.stderr, end="")
    if result.returncode != 0:
        print("\n>>> Pre-commit hooks failed – investigating manually.")

    print("\n>>> YAML sanity check")
    for path, exc in check_yaml_syntax():
        print(f"YAML error in {path}: {exc}")

    print("\n>>> JSON sanity check")
    for path, exc in check_json_syntax():
        print(f"JSON error in {path}: {exc}")

    if result.returncode == 0 and not check_yaml_syntax() and not check_json_syntax():
        print("\nAll validations passed!")
    else:
        print("\nPlease address the listed issues and rerun the script.")
        sys.exit(1)


if __name__ == "__main__":
    main()
