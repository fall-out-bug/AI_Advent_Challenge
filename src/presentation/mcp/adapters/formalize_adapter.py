"""Adapter for task formalization."""
import sys
from pathlib import Path
from typing import Any, Dict

_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "shared"))

from src.presentation.mcp.exceptions import MCPValidationError, MCPAgentError


def _get_model_client_adapter():
    """Import ModelClientAdapter at runtime to avoid circular imports."""
    from src.presentation.mcp.adapters.model_client_adapter import ModelClientAdapter
    return ModelClientAdapter


class FormalizeAdapter:
    """Adapter for converting informal tasks into structured plans."""

    def __init__(self, unified_client: Any, model_name: str) -> None:
        """Initialize adapter."""
        self.unified_client = unified_client
        self.model_name = model_name

    async def formalize(self, informal_request: str, context: str = "") -> Dict[str, Any]:
        """Formalize an informal task description."""
        self._validate_inputs(informal_request)

        try:
            ModelClientAdapter = _get_model_client_adapter()
            adapter = ModelClientAdapter(self.unified_client, model_name=self.model_name)
            prompt = self._build_prompt(informal_request, context)
            result = await adapter.generate(prompt=prompt, max_tokens=600, temperature=0.1)
            return self._parse_response(result.get("response", ""))
        except (MCPValidationError, MCPAgentError):
            raise
        except Exception as e:
            raise MCPAgentError(f"Formalization failed: {e}")

    def _validate_inputs(self, informal_request: str) -> None:
        """Validate inputs for formalization."""
        if not informal_request or not informal_request.strip():
            raise MCPValidationError("informal_request cannot be empty", field="informal_request")

    def _build_prompt(self, informal_request: str, context: str) -> str:
        """Build a deterministic, JSON-only prompt for the model."""
        return (
            "You are a senior software planner. Convert the user's request into a JSON plan.\n"
            "Return ONLY JSON with keys: formalized_description, requirements, steps, estimated_complexity.\n"
            "No commentary.\n\n"
            f"Request: {informal_request}\n"
            f"Context: {context}\n\n"
            "Example JSON: {\n"
            "  \"formalized_description\": \"...\",\n"
            "  \"requirements\": [\"...\"],\n"
            "  \"steps\": [\"...\"],\n"
            "  \"estimated_complexity\": \"low|medium|high\"\n"
            "}"
        )

    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parse model response into structured dict with safe defaults."""
        import json
        try:
            data = json.loads(text)
            return {
                "success": True,
                "formalized_description": data.get("formalized_description", ""),
                "requirements": data.get("requirements", []),
                "steps": data.get("steps", []),
                "estimated_complexity": data.get("estimated_complexity", "unknown"),
            }
        except Exception:
            # Fallback minimal structure when model returned non-JSON
            return {
                "success": True,
                "formalized_description": text.strip()[:5000],
                "requirements": [],
                "steps": [],
                "estimated_complexity": "unknown",
            }


