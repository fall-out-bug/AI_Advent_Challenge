"""Facade adapter to bridge MCP tools to application layer."""
import sys
from pathlib import Path
from typing import Any, Dict

_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "shared"))

from src.presentation.mcp.adapters.model_adapter import ModelAdapter
from src.presentation.mcp.adapters.generation_adapter import GenerationAdapter
from src.presentation.mcp.adapters.review_adapter import ReviewAdapter
from src.presentation.mcp.adapters.orchestration_adapter import OrchestrationAdapter
from src.presentation.mcp.adapters.token_adapter import TokenAdapter
from src.presentation.mcp.adapters.formalize_adapter import FormalizeAdapter
from src.presentation.mcp.adapters.test_generation_adapter import TestGenerationAdapter
from src.presentation.mcp.adapters.format_adapter import FormatAdapter
from src.presentation.mcp.adapters.complexity_adapter import ComplexityAdapter


class ModelClientAdapter:
    """Adapter to make UnifiedModelClient compatible with BaseAgent interface."""

    def __init__(self, unified_client: Any, model_name: str = "starcoder"):
        """Initialize adapter."""
        self.unified_client = unified_client
        self.model_name = model_name

    async def generate(self, prompt: str, max_tokens: int = 1500, temperature: float = 0.3) -> dict:
        """Generate response compatible with BaseAgent interface."""
        response = await self.unified_client.make_request(
            model_name=self.model_name,
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
    """Facade that delegates to specialized adapters."""

    def __init__(self):
        """Initialize MCP application adapter."""
        # Import lazily to avoid circular dependencies
        from shared_package.clients.unified_client import UnifiedModelClient
        from src.domain.services.token_analyzer import TokenAnalyzer
        
        self.unified_client = UnifiedModelClient()
        self.token_analyzer = TokenAnalyzer()
        
        # Initialize specialized adapters
        self.model_adapter = ModelAdapter(self.unified_client)
        self.token_adapter = TokenAdapter(self.token_analyzer)
        self.generation_adapter = GenerationAdapter(
            self.unified_client, model_name="starcoder"
        )
        self.review_adapter = ReviewAdapter(
            self.unified_client, model_name="starcoder"
        )
        self.orchestration_adapter = OrchestrationAdapter(self.unified_client)
        self.formalize_adapter = FormalizeAdapter(self.unified_client, model_name="starcoder")
        self.test_generation_adapter = TestGenerationAdapter(self.unified_client, model_name="starcoder")
        self.format_adapter = FormatAdapter()
        self.complexity_adapter = ComplexityAdapter()

    async def list_available_models(self) -> Dict[str, Any]:
        """List all configured models."""
        return self.model_adapter.list_available_models()

    async def check_model_availability(self, model_name: str) -> Dict[str, bool]:
        """Check if model is available."""
        return await self.model_adapter.check_model_availability(model_name)

    async def generate_code_via_agent(self, description: str, model: str) -> Dict[str, Any]:
        """Generate code using CodeGeneratorAgent."""
        try:
            return await self.generation_adapter.generate_code(description, model)
        except Exception as e:
            return {
                "success": False,
                "code": "",
                "error": str(e),
                "metadata": {"model_used": model},
            }

    async def review_code_via_agent(self, code: str, model: str) -> Dict[str, Any]:
        """Review code using CodeReviewerAgent."""
        try:
            return await self.review_adapter.review_code(code, model)
        except Exception as e:
            return {
                "success": False,
                "review": "",
                "quality_score": 0,
                "error": str(e),
                "metadata": {"model_used": model},
            }

    async def formalize_task(self, informal_request: str, context: str = "") -> Dict[str, Any]:
        """Formalize an informal task description into a structured plan."""
        try:
            return await self.formalize_adapter.formalize(informal_request, context)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "formalized_description": "",
                "requirements": [],
                "steps": [],
                "estimated_complexity": "unknown",
            }

    async def orchestrate_generation_and_review(self, description: str, gen_model: str, review_model: str) -> Dict[str, Any]:
        """Full workflow via MultiAgentOrchestrator."""
        try:
            return await self.orchestration_adapter.orchestrate_generation_and_review(
                description, gen_model, review_model
            )
        except Exception as e:
            return {
                "success": False,
                "generation": {"code": "", "tests": ""},
                "review": {"score": 0, "issues": [], "recommendations": []},
                "workflow_time": 0.0,
                "error": str(e),
            }

    def count_text_tokens(self, text: str) -> Dict[str, int]:
        """Count tokens using TokenAnalyzer."""
        try:
            return self.token_adapter.count_text_tokens(text)
        except Exception as e:
            return {"count": 0, "error": str(e)}

    async def generate_tests(self, code: str, test_framework: str = "pytest", coverage_target: int = 80) -> Dict[str, Any]:
        """Generate tests for code."""
        try:
            return await self.test_generation_adapter.generate_tests(
                code, test_framework, coverage_target
            )
        except Exception as e:
            return {
                "success": False,
                "test_code": "",
                "test_count": 0,
                "coverage_estimate": 0,
                "test_cases": [],
                "error": str(e),
            }
    
    def format_code(self, code: str, formatter: str = "black", line_length: int = 100) -> Dict[str, Any]:
        """Format code."""
        try:
            return self.format_adapter.format_code(code, formatter, line_length)
        except Exception as e:
            return {
                "formatted_code": code,
                "changes_made": 0,
                "formatter_used": formatter,
                "error": str(e),
            }
    
    def analyze_complexity(self, code: str, detailed: bool = True) -> Dict[str, Any]:
        """Analyze code complexity."""
        try:
            return self.complexity_adapter.analyze_complexity(code, detailed)
        except Exception as e:
            return {
                "cyclomatic_complexity": 0,
                "cognitive_complexity": 0,
                "lines_of_code": 0,
                "maintainability_index": 0.0,
                "recommendations": [],
                "error": str(e),
            }

    async def close(self) -> None:
        """Cleanup resources."""
        await self.unified_client.close()

