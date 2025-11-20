"""Code quality checker using linters and formatters.

Following Clean Architecture principles and the Zen of Python.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class CodeQualityChecker:
    """Code quality checker using multiple linters and formatters.

    Purpose:
        Runs static analysis tools (flake8, pylint, mypy, black, isort)
        on codebase and aggregates results.

    Args:
        code_path: Path to code directory or file to check

    Example:
        checker = CodeQualityChecker("/path/to/code")
        results = checker.run_all_checks()
    """

    def __init__(self, code_path: Path):
        """Initialize code quality checker.

        Args:
            code_path: Path to code directory
        """
        self.code_path = (
            Path(code_path) if not isinstance(code_path, Path) else code_path
        )
        self.logger = logging.getLogger(__name__)

    def run_flake8(self) -> Dict[str, Any]:
        """Run flake8 linter.

        Returns:
            Dictionary with flake8 results
        """
        try:
            result = subprocess.run(
                ["flake8", str(self.code_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            issues = []
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        # Parse flake8 output: path:line:col: code message
                        parts = line.split(":", 3)
                        if len(parts) >= 4:
                            issues.append(
                                {
                                    "file": parts[0],
                                    "line": parts[1],
                                    "column": parts[2],
                                    "code": (
                                        parts[3].split()[0] if parts[3].split() else ""
                                    ),
                                    "message": parts[3].strip() if parts[3] else "",
                                }
                            )

            return {
                "tool": "flake8",
                "success": True,  # Tool ran successfully (returncode 0=no issues, 1=issues found)
                "issues_count": len(issues),
                "issues": issues,
                "stderr": result.stderr if result.stderr else None,
            }

        except subprocess.TimeoutExpired:
            self.logger.warning("flake8 timed out")
            return {
                "tool": "flake8",
                "success": False,
                "error": "Timeout",
                "issues_count": 0,
                "issues": [],
            }
        except FileNotFoundError:
            self.logger.warning("flake8 not found")
            return {
                "tool": "flake8",
                "success": False,
                "error": "Not installed",
                "issues_count": 0,
                "issues": [],
            }
        except Exception as e:
            self.logger.error(f"flake8 error: {e}")
            return {
                "tool": "flake8",
                "success": False,
                "error": str(e),
                "issues_count": 0,
                "issues": [],
            }

    def run_pylint(self) -> Dict[str, Any]:
        """Run pylint linter.

        Returns:
            Dictionary with pylint results
        """
        try:
            # Find all Python files
            python_files = list(self.code_path.rglob("*.py"))
            if not python_files:
                return {
                    "tool": "pylint",
                    "success": True,
                    "score": 10.0,
                    "issues_count": 0,
                    "issues": [],
                    "note": "No Python files found",
                }

            # Run pylint on all files
            result = subprocess.run(
                ["pylint"] + [str(f) for f in python_files[:10]],  # Limit to 10 files
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Parse score from output
            score = None
            for line in result.stdout.split("\n"):
                if "Your code has been rated at" in line:
                    try:
                        score_str = line.split("rated at")[1].split("/")[0].strip()
                        score = float(score_str)
                    except (IndexError, ValueError):
                        pass
                    break

            # Parse issues
            issues = []
            if result.stdout:
                for line in result.stdout.split("\n"):
                    if ": C" in line or ": E" in line or ": W" in line or ": R" in line:
                        issues.append(line.strip())

            return {
                "tool": "pylint",
                "success": True,
                "score": score,
                "issues_count": len(issues),
                "issues": issues[:50],  # Limit to 50 issues
                "stderr": result.stderr if result.stderr else None,
            }

        except subprocess.TimeoutExpired:
            self.logger.warning("pylint timed out")
            return {
                "tool": "pylint",
                "success": False,
                "error": "Timeout",
                "score": None,
                "issues_count": 0,
                "issues": [],
            }
        except FileNotFoundError:
            self.logger.warning("pylint not found")
            return {
                "tool": "pylint",
                "success": False,
                "error": "Not installed",
                "score": None,
                "issues_count": 0,
                "issues": [],
            }
        except Exception as e:
            self.logger.error(f"pylint error: {e}")
            return {
                "tool": "pylint",
                "success": False,
                "error": str(e),
                "score": None,
                "issues_count": 0,
                "issues": [],
            }

    def run_mypy(self) -> Dict[str, Any]:
        """Run mypy type checker.

        Returns:
            Dictionary with mypy results
        """
        try:
            # Find all Python files
            python_files = list(self.code_path.rglob("*.py"))
            if not python_files:
                return {
                    "tool": "mypy",
                    "success": True,
                    "files_checked": 0,
                    "errors": 0,
                    "issues": [],
                    "note": "No Python files found",
                }

            # Run mypy
            result = subprocess.run(
                ["mypy"] + [str(f) for f in python_files[:10]],
                capture_output=True,
                text=True,
                timeout=120,
            )

            errors = []
            if result.stdout:
                for line in result.stdout.split("\n"):
                    if "error:" in line:
                        errors.append(line.strip())

            return {
                "tool": "mypy",
                "success": True,  # Tool ran successfully (returncode 0=no issues, 1=issues found)
                "files_checked": len(python_files[:10]),
                "errors": len(errors),
                "issues": errors[:50],  # Limit to 50 errors
                "stderr": result.stderr if result.stderr else None,
            }

        except subprocess.TimeoutExpired:
            self.logger.warning("mypy timed out")
            return {
                "tool": "mypy",
                "success": False,
                "error": "Timeout",
                "files_checked": 0,
                "errors": 0,
                "issues": [],
            }
        except FileNotFoundError:
            self.logger.warning("mypy not found")
            return {
                "tool": "mypy",
                "success": False,
                "error": "Not installed",
                "files_checked": 0,
                "errors": 0,
                "issues": [],
            }
        except Exception as e:
            self.logger.error(f"mypy error: {e}")
            return {
                "tool": "mypy",
                "success": False,
                "error": str(e),
                "files_checked": 0,
                "errors": 0,
                "issues": [],
            }

    def run_black(self) -> Dict[str, Any]:
        """Run black formatter check.

        Returns:
            Dictionary with black results
        """
        try:
            # Find all Python files
            python_files = list(self.code_path.rglob("*.py"))
            if not python_files:
                return {
                    "tool": "black",
                    "success": True,
                    "needs_reformatting": 0,
                    "files_checked": 0,
                    "note": "No Python files found",
                }

            # Run black in check mode
            result = subprocess.run(
                ["black", "--check", "--diff"] + [str(f) for f in python_files[:10]],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Count files needing reformatting
            needs_reformatting = result.stdout.count("would reformat")

            return {
                "tool": "black",
                "success": True,  # Tool ran successfully (returncode 0=no issues, 1=issues found)
                "files_checked": len(python_files[:10]),
                "needs_reformatting": needs_reformatting,
                "diff": result.stdout if result.stdout else None,
            }

        except subprocess.TimeoutExpired:
            self.logger.warning("black timed out")
            return {
                "tool": "black",
                "success": False,
                "error": "Timeout",
                "files_checked": 0,
                "needs_reformatting": 0,
            }
        except FileNotFoundError:
            self.logger.warning("black not found")
            return {
                "tool": "black",
                "success": False,
                "error": "Not installed",
                "files_checked": 0,
                "needs_reformatting": 0,
            }
        except Exception as e:
            self.logger.error(f"black error: {e}")
            return {
                "tool": "black",
                "success": False,
                "error": str(e),
                "files_checked": 0,
                "needs_reformatting": 0,
            }

    def run_isort(self) -> Dict[str, Any]:
        """Run isort import sorter check.

        Returns:
            Dictionary with isort results
        """
        try:
            # Find all Python files
            python_files = list(self.code_path.rglob("*.py"))
            if not python_files:
                return {
                    "tool": "isort",
                    "success": True,
                    "needs_sorting": 0,
                    "files_checked": 0,
                    "note": "No Python files found",
                }

            # Run isort in check mode
            result = subprocess.run(
                ["isort", "--check-only", "--diff"]
                + [str(f) for f in python_files[:10]],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Count files needing sorting
            needs_sorting = result.stdout.count("would reformat")

            return {
                "tool": "isort",
                "success": True,  # Tool ran successfully (returncode 0=no issues, 1=issues found)
                "files_checked": len(python_files[:10]),
                "needs_sorting": needs_sorting,
                "diff": result.stdout if result.stdout else None,
            }

        except subprocess.TimeoutExpired:
            self.logger.warning("isort timed out")
            return {
                "tool": "isort",
                "success": False,
                "error": "Timeout",
                "files_checked": 0,
                "needs_sorting": 0,
            }
        except FileNotFoundError:
            self.logger.warning("isort not found")
            return {
                "tool": "isort",
                "success": False,
                "error": "Not installed",
                "files_checked": 0,
                "needs_sorting": 0,
            }
        except Exception as e:
            self.logger.error(f"isort error: {e}")
            return {
                "tool": "isort",
                "success": False,
                "error": str(e),
                "files_checked": 0,
                "needs_sorting": 0,
            }

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all code quality checks.

        Returns:
            Dictionary with aggregated results from all tools
        """
        self.logger.info("Running all code quality checks...")

        results = {
            "flake8": self.run_flake8(),
            "pylint": self.run_pylint(),
            "mypy": self.run_mypy(),
            "black": self.run_black(),
            "isort": self.run_isort(),
        }

        # Calculate summary statistics
        total_issues = sum(
            result.get("issues_count", 0) + result.get("errors", 0)
            for result in results.values()
            if isinstance(result, dict)
        )

        return {
            "tools": results,
            "summary": {
                "total_issues": total_issues,
                "tools_run": len(results),
                "tools_successful": sum(
                    1 for r in results.values() if r.get("success", False)
                ),
            },
        }
