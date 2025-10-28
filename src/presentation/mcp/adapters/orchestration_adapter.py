"""Adapter for multi-agent orchestration operations."""
import sys
from pathlib import Path
from typing import Any, Optional

_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "shared"))

from src.domain.agents.code_generator import CodeGeneratorAgent
from src.domain.agents.code_reviewer import CodeReviewerAgent
from src.application.orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator
from src.domain.messaging.message_schema import OrchestratorRequest
from src.presentation.mcp.exceptions import MCPOrchestrationError, MCPValidationError


def _get_model_client_adapter():
    """Import ModelClientAdapter at runtime to avoid circular imports."""
    from src.presentation.mcp.adapters.model_client_adapter import ModelClientAdapter
    return ModelClientAdapter


class OrchestrationAdapter:
    """Adapter for full generate-and-review workflows."""

    def __init__(self, unified_client: Any) -> None:
        """Initialize orchestration adapter."""
        self.unified_client = unified_client

    async def orchestrate_generation_and_review(self, description: str, gen_model: str, review_model: str) -> dict[str, Any]:
        """Execute full workflow via MultiAgentOrchestrator."""
        try:
            self._validate_inputs(description, gen_model, review_model)
            return await self._execute_workflow(description, gen_model, review_model)
        except (MCPValidationError, MCPOrchestrationError):
            raise
        except Exception as e:
            raise MCPOrchestrationError(f"Orchestration failed: {e}")

    def _validate_inputs(self, description: str, gen_model: str, review_model: str) -> None:
        """Validate workflow inputs."""
        if not description or not description.strip():
            raise MCPValidationError("Description cannot be empty", field="description")
        if not gen_model or not gen_model.strip():
            raise MCPValidationError("Generation model cannot be empty", field="gen_model")
        if not review_model or not review_model.strip():
            raise MCPValidationError("Review model cannot be empty", field="review_model")

    async def _execute_workflow(self, description: str, gen_model: str, review_model: str) -> dict[str, Any]:
        """Execute the orchestration workflow."""
        try:
            agents = self._create_agents(gen_model, review_model)
            orchestrator = MultiAgentOrchestrator(
                generator_agent=agents["generator"],
                reviewer_agent=agents["reviewer"],
            )
            request = self._create_request(description, gen_model, review_model)
            result = await orchestrator.process_task(request)
            return self._build_response(result)
        except Exception as e:
            raise MCPOrchestrationError(
                f"Workflow execution failed: {e}", stage="execution"
            )

    def _create_agents(self, gen_model: str, review_model: str) -> dict[str, Any]:
        """Create generator and reviewer agents."""
        ModelClientAdapter = _get_model_client_adapter()
        generator_adapter = ModelClientAdapter(
            self.unified_client, model_name=gen_model
        )
        reviewer_adapter = ModelClientAdapter(
            self.unified_client, model_name=review_model
        )

        return {
            "generator": CodeGeneratorAgent(model_client=generator_adapter),
            "reviewer": CodeReviewerAgent(model_client=reviewer_adapter),
        }

    def _create_request(self, description: str, gen_model: str, review_model: str) -> OrchestratorRequest:
        """Create orchestrator request."""
        return OrchestratorRequest(
            task_description=description,
            requirements=["Include type hints", "Include docstrings", "Follow PEP8"],
            language="python",
            model_name=gen_model,
            reviewer_model_name=review_model,
        )

    def _build_response(self, result: Any) -> dict[str, Any]:
        """Build response dictionary."""
        gen = result.generation_result if result.success else None
        rev = result.review_result if result.success else None

        return {
            "success": result.success,
            "generation": {
                "code": gen.generated_code if gen else "",
                "tests": gen.tests if gen else "",
            },
            "review": {
                "score": rev.code_quality_score if rev else 0,
                "issues": rev.issues if rev else [],
                "recommendations": rev.recommendations if rev else [],
            },
            "workflow_time": result.workflow_time,
            "error": None if result.success else "Workflow failed",
        }
