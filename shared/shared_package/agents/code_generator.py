"""
Code generation agent.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import logging
from typing import Optional

from .base_agent import BaseAgent
from ..clients.unified_client import UnifiedModelClient
from .schemas import AgentRequest, AgentResponse, TaskMetadata


logger = logging.getLogger(__name__)


class CodeGeneratorAgent(BaseAgent):
    """
    Code generation agent for creating code from specifications.
    
    Following Python Zen: "Simple is better than complex"
    and "Explicit is better than implicit".
    
    This agent generates code based on task descriptions,
    supporting multiple programming languages and styles.
    """
    
    def __init__(
        self, 
        client: UnifiedModelClient,
        model_name: str = "gpt-4",
        max_tokens: int = 2000,
        temperature: float = 0.7
    ):
        """
        Initialize code generator agent.
        
        Args:
            client: UnifiedModelClient instance
            model_name: Model to use for generation
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
        """
        super().__init__(client, "code_generator")
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    async def _process_impl(self, request: AgentRequest) -> AgentResponse:
        """
        Generate code from specification.
        
        Args:
            request: Agent request with task description
            
        Returns:
            AgentResponse: Generated code
            
        Raises:
            Exception: If generation fails
        """
        prompt = self._build_prompt(request)
        model_response = await self._call_model(
            prompt=prompt,
            model_name=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        generated_code = self._parse_response(model_response.response)
        
        metadata = self._create_metadata(
            task_type="code_generation",
            model_name=self.model_name
        )
        
        return AgentResponse(
            result=generated_code,
            success=True,
            error=None,
            metadata=metadata,
            quality=None
        )
    
    def _build_prompt(self, request: AgentRequest) -> str:
        """
        Build prompt for code generation.
        
        Args:
            request: Agent request
            
        Returns:
            str: Formatted prompt
        """
        language = request.context.get("language", "python") if request.context else "python"
        style = request.context.get("style", "clean") if request.context else "clean"
        
        prompt = f"""Generate {language} code for the following specification:
        
{request.task}

Requirements:
- Language: {language}
- Style: {style}
- Follow best practices and PEP 8 (if applicable)
- Include docstrings and type hints
- Make the code clear, concise, and maintainable

Return only the code without explanations:"""
        
        return prompt
    
    def _parse_response(self, response: str) -> str:
        """
        Parse and clean model response.
        
        Args:
            response: Raw model response
            
        Returns:
            str: Cleaned code
        """
        # Remove markdown code blocks if present
        if response.startswith("```"):
            lines = response.split("\n")
            # Remove first line (```python or similar)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response = "\n".join(lines)
        
        return response.strip()
    
    def set_model(self, model_name: str) -> None:
        """
        Set model for code generation.
        
        Args:
            model_name: Model name
        """
        self.model_name = model_name
        logger.info(f"CodeGeneratorAgent model set to: {model_name}")
    
    def set_parameters(
        self, 
        max_tokens: Optional[int] = None, 
        temperature: Optional[float] = None
    ) -> None:
        """
        Set generation parameters.
        
        Args:
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
        """
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if temperature is not None:
            self.temperature = temperature
        logger.info(f"CodeGeneratorAgent parameters updated: max_tokens={self.max_tokens}, temperature={self.temperature}")
