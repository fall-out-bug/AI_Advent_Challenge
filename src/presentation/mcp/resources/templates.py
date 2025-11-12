"""MCP resource: Project structure and code templates.

Following Python Zen: "Simple is better than complex."
"""


def get_project_structure_template() -> str:
    """Return standard Python project structure template.

    Returns:
        Project structure template
    """
    return """project/
├── src/
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   └── entities/
│   ├── application/
│   │   ├── __init__.py
│   │   └── use_cases/
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   └── repositories/
│   └── presentation/
│       ├── __init__.py
│       └── api/
├── tests/
│   ├── __init__.py
│   ├── unit/
│   └── integration/
├── docs/
├── pyproject.toml
└── README.md"""


def get_pytest_template() -> str:
    """Return pytest test file template.

    Returns:
        Pytest test template
    """
    return """\"\"\"Tests for {module_name}.
\"\"\"
import pytest
from {module_path} import {class_or_function_name}


class Test{class_or_function_name}:
    \"\"\"Test suite for {class_or_function_name}.\"\"\"

    def test_{method_name}_success(self):
        \"\"\"Test {method_name} with valid inputs.\"\"\"
        # Arrange
        # Act
        # Assert
        pass

    def test_{method_name}_error(self):
        \"\"\"Test {method_name} with invalid inputs.\"\"\"
        # Arrange
        # Act
        # Assert
        pass"""


def get_class_template() -> str:
    """Return Python class template.

    Returns:
        Python class template
    """
    return """\"\"\"{class_name} class.
\"\"\"
from typing import Any, Dict, Optional


class {class_name}:
    \"\"\"{class_description}\"\"\"

    def __init__(self, param: str) -> None:
        \"\"\"Initialize {class_name}.

        Args:
            param: Parameter description
        \"\"\"
        self.param = param

    def method(self, arg: Any) -> Dict[str, Any]:
        \"\"\"Method description.

        Args:
            arg: Argument description

        Returns:
            Dictionary with results

        Raises:
            ValueError: If arg is invalid
        \"\"\"
        if not arg:
            raise ValueError("arg cannot be empty")

        return {{"result": "success"}}"""
