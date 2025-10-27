"""Adapter for code review operations."""
import sys
from pathlib import Path
from typing import Any, Optional

# Add root to path
_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))
shared_path = _root / "shared"
sys.path.insert(0, str(shared_path))

from src.domain.agents.code_reviewer import CodeReviewerAgent
from src.domain.agents.base_agent import TaskMetadata
from src.domain.messaging.message_schema import CodeReviewRequest
from src.presentation.mcp.exceptions import MCPAgentError, MCPValidationError


def _get_model_client_adapter():
    """Import ModelClientAdapter at runtime to avoid circular imports."""
    from src.presentation.mcp.adapters.model_client_adapter import ModelClientAdapter
    return ModelClientAdapter


class ReviewAdapter:
    """Adapter for code review operations."""

    def __init__(
        self,
        unified_client: Any,
        model_name: str,
    ) -> None:
        """Initialize review adapter.

        Args:
            unified_client: Unified model client instance
            model_name: Default model to use
        """
        self.unified_client = unified_client
        self.model_name = model_name

    async def review_code(
        self, code: str, model: Optional[str] = None
    ) -> dict[str, Any]:
        """Review code using CodeReviewerAgent.

        Args:
            code: Python code to review
            model: Model to use (defaults to adapter's model)

        Returns:
            Dictionary with review results and quality score

        Raises:
            MCPValidationError: If input is invalid
            MCPAgentError: If review fails
        """
        try:
            self._validate_code(code)
            model_to_use = model or self.model_name
            ModelClientAdapter = _get_model_client_adapter()
            adapter = ModelClientAdapter(self.unified_client, model_name=model_to_use)
            agent = CodeReviewerAgent(model_client=adapter, model_name=model_to_use)
            request = self._create_request(code)
            response = await agent.process(request)
            return self._build_response(response, model_to_use)
        except (MCPValidationError, MCPAgentError):
            raise
        except Exception as e:
            raise MCPAgentError(f"Code review failed: {e}", agent_type="reviewer")

    def _validate_code(self, code: str) -> None:
        """Validate code input.

        Args:
            code: Code to validate

        Raises:
            MCPValidationError: If code is invalid
        """
        if not code or not code.strip():
            raise MCPValidationError("Code cannot be empty", field="code")

    def _create_request(self, code: str) -> CodeReviewRequest:
        """Create review request.

        Args:
            code: Code to review

        Returns:
            Code review request
        """
        # Create empty metadata dict instead of object
        metadata = {}
        
        return CodeReviewRequest(
            task_description="Code review",
            generated_code=code,
            tests="",
            metadata=metadata,
        )

    def _build_response(self, response: Any, model: str) -> dict[str, Any]:
        """Build response dictionary.

        Args:
            response: Agent response
            model: Model used

        Returns:
            Response dictionary
        """
        return {
            "success": True,
            "quality_score": response.code_quality_score,
            "issues": response.issues,
            "recommendations": response.recommendations,
            "review": f"Quality score: {response.code_quality_score}/10",
            "metadata": {"model_used": model},
        }
