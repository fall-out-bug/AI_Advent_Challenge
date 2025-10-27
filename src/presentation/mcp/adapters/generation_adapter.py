"""Adapter for code generation operations."""
import sys
from pathlib import Path
from typing import Any, Optional

# Add root to path
_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))
shared_path = _root / "shared"
sys.path.insert(0, str(shared_path))

from src.domain.agents.code_generator import CodeGeneratorAgent
from src.domain.agents.base_agent import TaskMetadata
from src.domain.messaging.message_schema import CodeGenerationRequest
from src.presentation.mcp.exceptions import MCPAgentError, MCPValidationError


def _get_model_client_adapter():
    """Import ModelClientAdapter at runtime to avoid circular imports."""
    from src.presentation.mcp.adapters.model_client_adapter import ModelClientAdapter
    return ModelClientAdapter


class GenerationAdapter:
    """Adapter for code generation operations."""

    def __init__(
        self,
        unified_client: Any,
        model_name: str,
    ) -> None:
        """Initialize generation adapter.

        Args:
            unified_client: Unified model client instance
            model_name: Default model to use
        """
        self.unified_client = unified_client
        self.model_name = model_name

    async def generate_code(
        self, description: str, model: Optional[str] = None
    ) -> dict[str, Any]:
        """Generate code using CodeGeneratorAgent.

        Args:
            description: Description of code to generate
            model: Model to use (defaults to adapter's model)

        Returns:
            Dictionary with generated code and metadata

        Raises:
            MCPValidationError: If input is invalid
            MCPAgentError: If generation fails
        """
        try:
            self._validate_description(description)
            model_to_use = model or self.model_name
            ModelClientAdapter = _get_model_client_adapter()
            adapter = ModelClientAdapter(self.unified_client, model_name=model_to_use)
            agent = CodeGeneratorAgent(model_client=adapter, model_name=model_to_use)
            request = self._create_request(description, model_to_use)
            response = await agent.process(request)
            return self._build_response(response, model_to_use)
        except (MCPValidationError, MCPAgentError):
            raise
        except Exception as e:
            raise MCPAgentError(
                f"Code generation failed: {e}",
                agent_type="generator",
            )

    def _validate_description(self, description: str) -> None:
        """Validate description input.

        Args:
            description: Description to validate

        Raises:
            MCPValidationError: If description is invalid
        """
        if not description or not description.strip():
            raise MCPValidationError(
                "Description cannot be empty", field="description"
            )

    def _create_request(self, description: str, model: str) -> CodeGenerationRequest:
        """Create generation request.

        Args:
            description: Task description
            model: Model to use

        Returns:
            Code generation request
        """
        return CodeGenerationRequest(
            task_description=description,
            language="python",
            model_name=model,
        )

    def _build_response(
        self, response: Any, model: str
    ) -> dict[str, Any]:
        """Build response dictionary.

        Args:
            response: Agent response
            model: Model used

        Returns:
            Response dictionary
        """
        return {
            "success": True,
            "code": response.generated_code,
            "tests": response.tests,
            "metadata": {
                "complexity": response.metadata.complexity,
                "lines_of_code": response.metadata.lines_of_code,
                "model_used": model,
            },
        }
