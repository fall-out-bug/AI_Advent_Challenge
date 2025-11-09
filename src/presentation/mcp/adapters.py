"""Facade adapter that exposes MCP capabilities via specialised adapters."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from shared.shared_package.clients.unified_client import UnifiedModelClient
from src.domain.services.token_analyzer import TokenAnalyzer
from src.presentation.mcp.adapters.complexity_adapter import ComplexityAdapter
from src.presentation.mcp.adapters.formalize_adapter import FormalizeAdapter
from src.presentation.mcp.adapters.format_adapter import FormatAdapter
from src.presentation.mcp.adapters.generation_adapter import GenerationAdapter
from src.presentation.mcp.adapters.model_adapter import ModelAdapter
from src.presentation.mcp.adapters.orchestration_adapter import OrchestrationAdapter
from src.presentation.mcp.adapters.review_adapter import ReviewAdapter
from src.presentation.mcp.adapters.test_generation_adapter import TestGenerationAdapter
from src.presentation.mcp.adapters.token_adapter import TokenAdapter


class ModelClientAdapter:
    """Expose ``UnifiedModelClient`` via a minimal BaseAgent-like interface."""

    def __init__(
        self, unified_client: UnifiedModelClient, model_name: str = "starcoder"
    ) -> None:
        self._unified_client = unified_client
        self._model_name = model_name

    async def generate(
        self, prompt: str, max_tokens: int = 1500, temperature: float = 0.3
    ) -> dict[str, Any]:
        """Return a response payload matching the legacy BaseAgent contract."""

        response = await self._unified_client.make_request(
            model_name=self._model_name,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return {
            "response": response.response,
            "total_tokens": response.total_tokens,
            "input_tokens": response.input_tokens,
            "response_tokens": response.response_tokens,
        }


class MCPApplicationAdapter:
    """Facade orchestrating the individual MCP adapters used by the bot."""

    def __init__(
        self,
        unified_client: Optional[UnifiedModelClient] = None,
        token_analyzer: Optional[TokenAnalyzer] = None,
    ) -> None:
        self._unified_client = unified_client or UnifiedModelClient()
        self._token_analyzer = token_analyzer or TokenAnalyzer()

        self._model_adapter = ModelAdapter(self._unified_client)
        self._token_adapter = TokenAdapter(self._token_analyzer)
        self._generation_adapter = GenerationAdapter(
            self._unified_client, model_name="starcoder"
        )
        self._review_adapter = ReviewAdapter(
            self._unified_client, model_name="starcoder"
        )
        self._orchestration_adapter = OrchestrationAdapter(self._unified_client)
        self._formalize_adapter = FormalizeAdapter(
            self._unified_client, model_name="starcoder"
        )
        self._test_generation_adapter = TestGenerationAdapter(
            self._unified_client, model_name="starcoder"
        )
        self._format_adapter = FormatAdapter()
        self._complexity_adapter = ComplexityAdapter()

    async def list_available_models(self) -> dict[str, Any]:
        """Return all configured model descriptors."""

        return self._model_adapter.list_available_models()

    async def check_model_availability(
        self,
        model_name: str,
    ) -> dict[str, bool]:
        """Return availability metadata for ``model_name``."""

        return await self._model_adapter.check_model_availability(model_name)

    async def generate_code_via_agent(
        self, description: str, model: str
    ) -> dict[str, Any]:
        """Delegate to the code generation adapter with error wrapping."""

        try:
            return await self._generation_adapter.generate_code(description, model)
        except Exception as error:  # noqa: BLE001
            return {
                "success": False,
                "code": "",
                "error": str(error),
                "metadata": {"model_used": model},
            }

    async def review_code_via_agent(
        self,
        code: str,
        model: str,
    ) -> dict[str, Any]:
        """Run the review adapter while preserving legacy response shape."""

        try:
            return await self._review_adapter.review_code(code, model)
        except Exception as error:  # noqa: BLE001
            return {
                "success": False,
                "review": "",
                "quality_score": 0,
                "error": str(error),
                "metadata": {"model_used": model},
            }

    async def formalize_task(
        self, informal_request: str, context: str = ""
    ) -> dict[str, Any]:
        """Formalise free-form input through the planner adapter."""

        try:
            return await self._formalize_adapter.formalize(
                informal_request,
                context,
            )
        except Exception as error:  # noqa: BLE001
            return {
                "success": False,
                "error": str(error),
                "formalized_description": "",
                "requirements": [],
                "steps": [],
                "estimated_complexity": "unknown",
            }

    async def orchestrate_generation_and_review(
        self,
        description: str,
        gen_model: str,
        review_model: str,
    ) -> dict[str, Any]:
        """Run the orchestrator and keep the legacy payload structure."""

        try:
            orchestrate = self._orchestration_adapter.orchestrate_generation_and_review
            return await orchestrate(
                description,
                gen_model,
                review_model,
            )
        except Exception as error:  # noqa: BLE001
            return {
                "success": False,
                "generation": {"code": "", "tests": ""},
                "review": {"score": 0, "issues": [], "recommendations": []},
                "workflow_time": 0.0,
                "error": str(error),
            }

    def count_text_tokens(self, text: str) -> Mapping[str, int | str]:
        """Return token counts or a descriptive error payload."""

        try:
            return self._token_adapter.count_text_tokens(text)
        except Exception as error:  # noqa: BLE001
            return {"count": 0, "error": str(error)}

    async def generate_tests(
        self,
        code: str,
        test_framework: str = "pytest",
        coverage_target: int = 80,
    ) -> dict[str, Any]:
        """Produce test cases for ``code`` with graceful degradation."""

        try:
            return await self._test_generation_adapter.generate_tests(
                code, test_framework, coverage_target
            )
        except Exception as error:  # noqa: BLE001
            return {
                "success": False,
                "test_code": "",
                "test_count": 0,
                "coverage_estimate": 0,
                "test_cases": [],
                "error": str(error),
            }

    def format_code(
        self,
        code: str,
        formatter: str = "black",
        line_length: int = 100,
    ) -> dict[str, Any]:
        """Apply the configured formatter and guard against failures."""

        try:
            return self._format_adapter.format_code(
                code,
                formatter,
                line_length,
            )
        except Exception as error:  # noqa: BLE001
            return {
                "formatted_code": code,
                "changes_made": 0,
                "formatter_used": formatter,
                "error": str(error),
            }

    def analyze_complexity(
        self,
        code: str,
        detailed: bool = True,
    ) -> dict[str, Any]:
        """Delegate to the complexity adapter, mirroring the legacy payload."""

        try:
            return self._complexity_adapter.analyze_complexity(code, detailed)
        except Exception as error:  # noqa: BLE001
            return {
                "cyclomatic_complexity": 0,
                "cognitive_complexity": 0,
                "lines_of_code": 0,
                "maintainability_index": 0.0,
                "recommendations": [],
                "error": str(error),
            }

    async def close(self) -> None:
        """Release resources owned by the unified client."""

        await self._unified_client.close()
