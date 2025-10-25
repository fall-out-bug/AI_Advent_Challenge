"""
Code Generator Adapter for integrating day_07 CodeGeneratorAgent.

This module provides the CodeGeneratorAdapter class that wraps the day_07
CodeGeneratorAgent and integrates it with day_08's token counting,
compression, and analysis capabilities.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add day_07 to path for importing agents
day_07_path = Path(__file__).parent.parent.parent / "day_07"
sys.path.insert(0, str(day_07_path))

try:
    from agents.core.code_generator import CodeGeneratorAgent
    from communication.message_schema import (
        CodeGenerationRequest,
        CodeGenerationResponse,
        TaskMetadata
    )
except ImportError:
    # Fallback for when day_07 agents are not available
    CodeGeneratorAgent = None
    CodeGenerationRequest = None
    CodeGenerationResponse = None
    TaskMetadata = None

from core.ml_client import TokenAnalysisClient
from core.token_analyzer import SimpleTokenCounter
from core.text_compressor import SimpleTextCompressor
from models.data_models import ExperimentResult
from utils.logging import LoggerFactory

# Configure logging
logger = LoggerFactory.create_logger(__name__)


class CodeGeneratorAdapter:
    """
    Adapter for day_07 CodeGeneratorAgent with day_08 integration.
    
    Wraps the day_07 CodeGeneratorAgent and integrates it with day_08's
    token counting, compression, and analysis capabilities.
    
    Attributes:
        generator_agent: day_07 CodeGeneratorAgent instance
        model_client: TokenAnalysisClient for model interactions
        token_counter: TokenCounter for token counting
        text_compressor: TextCompressor for compression
        logger: Logger instance for structured logging
        
    Example:
        ```python
        from agents.code_generator_adapter import CodeGeneratorAdapter
        from core.ml_client import TokenAnalysisClient
        from core.token_analyzer import SimpleTokenCounter
        from core.text_compressor import SimpleTextCompressor
        
        # Initialize adapter
        model_client = TokenAnalysisClient()
        token_counter = SimpleTokenCounter()
        text_compressor = SimpleTextCompressor(token_counter)
        
        adapter = CodeGeneratorAdapter(
            model_client=model_client,
            token_counter=token_counter,
            text_compressor=text_compressor
        )
        
        # Generate code with compression
        result = await adapter.generate_code_with_compression(
            task_description="Write a sorting function",
            model_name="starcoder",
            max_tokens=1000
        )
        ```
    """
    
    def __init__(
        self,
        model_client: Optional[TokenAnalysisClient] = None,
        token_counter: Optional[SimpleTokenCounter] = None,
        text_compressor: Optional[SimpleTextCompressor] = None,
        model_name: str = "starcoder"
    ):
        """
        Initialize the code generator adapter.
        
        Args:
            model_client: Optional TokenAnalysisClient instance
            token_counter: Optional TokenCounter instance
            text_compressor: Optional TextCompressor instance
            model_name: Default model name to use
            
        Example:
            ```python
            from agents.code_generator_adapter import CodeGeneratorAdapter
            
            # Initialize with default components
            adapter = CodeGeneratorAdapter()
            
            # Or with custom components
            adapter = CodeGeneratorAdapter(
                model_client=custom_client,
                token_counter=custom_counter,
                text_compressor=custom_compressor,
                model_name="mistral"
            )
            ```
        """
        self.model_client = model_client or TokenAnalysisClient()
        self.token_counter = token_counter or SimpleTokenCounter()
        self.text_compressor = text_compressor or SimpleTextCompressor(self.token_counter)
        self.logger = LoggerFactory.create_logger(__name__)
        
        # Initialize day_07 generator agent if available
        if CodeGeneratorAgent:
            try:
                self.generator_agent = CodeGeneratorAgent(
                    model_name=model_name,
                    max_tokens=2000,
                    temperature=0.7
                )
                self.logger.info(f"Initialized CodeGeneratorAgent with {model_name}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize CodeGeneratorAgent: {e}")
                self.generator_agent = None
        else:
            self.generator_agent = None
            self.logger.warning("CodeGeneratorAgent not available")
        
        self.logger.info("Initialized CodeGeneratorAdapter")
    
    async def generate_code_with_compression(
        self,
        task_description: str,
        model_name: str,
        max_tokens: int = 1000,
        compression_strategy: str = "truncation",
        language: str = "python",
        requirements: Optional[List[str]] = None
    ) -> ExperimentResult:
        """
        Generate code with automatic compression if needed.
        
        Args:
            task_description: Description of the coding task
            model_name: Name of the model to use
            max_tokens: Maximum tokens for generation
            compression_strategy: Compression strategy to use if needed
            language: Programming language
            requirements: Additional requirements
            
        Returns:
            ExperimentResult containing generation results
            
        Example:
            ```python
            # Generate code with compression
            result = await adapter.generate_code_with_compression(
                task_description="Implement a binary search tree",
                model_name="starcoder",
                max_tokens=1500,
                compression_strategy="keywords"
            )
            
            print(f"Success: {result.success}")
            print(f"Tokens used: {result.total_tokens}")
            if result.compression_result:
                print(f"Compression ratio: {result.compression_result.compression_ratio}")
            ```
        """
        try:
            self.logger.info(f"Generating code for: {task_description[:50]}...")
            
            # Check if task exceeds token limits
            model_limits = self.token_counter.get_model_limits(model_name)
            task_tokens = self.token_counter.count_tokens(task_description, model_name).count
            
            processed_query = task_description
            compression_result = None
            
            # Apply compression if needed
            if task_tokens > model_limits.max_input_tokens:
                self.logger.info(f"Task exceeds limit ({task_tokens} > {model_limits.max_input_tokens}), applying compression...")
                
                compression_result = self.text_compressor.compress_text(
                    text=task_description,
                    max_tokens=model_limits.recommended_input or model_limits.max_input_tokens,
                    model_name=model_name,
                    strategy=compression_strategy
                )
                
                processed_query = compression_result.compressed_text
                self.logger.info(f"Compressed from {compression_result.original_tokens} to {compression_result.compressed_tokens} tokens")
            
            # Generate code using day_07 agent or fallback
            if self.generator_agent:
                response = await self._generate_with_day_07_agent(
                    processed_query, model_name, max_tokens, language, requirements
                )
            else:
                response = await self._generate_with_fallback(
                    processed_query, model_name, max_tokens
                )
            
            # Count tokens
            input_tokens = self.token_counter.count_tokens(processed_query, model_name).count
            output_tokens = self.token_counter.count_tokens(response, model_name).count
            
            return ExperimentResult(
                experiment_name="code_generation_with_compression",
                model_name=model_name,
                original_query=task_description,
                processed_query=processed_query,
                response=response,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                response_time=0.0,  # Will be updated by caller
                compression_applied=compression_result is not None,
                compression_result=compression_result
            )
            
        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            
            return ExperimentResult(
                experiment_name="code_generation_with_compression",
                model_name=model_name,
                original_query=task_description,
                processed_query=task_description,
                response="",
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                response_time=0.0,
                compression_applied=False,
                compression_result=None,
                success=False,
                error_message=str(e)
            )
    
    async def _generate_with_day_07_agent(
        self,
        query: str,
        model_name: str,
        max_tokens: int,
        language: str,
        requirements: Optional[List[str]]
    ) -> str:
        """Generate code using day_07 CodeGeneratorAgent."""
        try:
            # Create request for day_07 agent
            request = CodeGenerationRequest(
                task_description=query,
                language=language,
                requirements=requirements or [],
                model_name=model_name
            )
            
            # Generate code
            response = await self.generator_agent.process(request)
            
            # Extract code from response
            generated_code = response.generated_code
            tests = response.tests
            
            # Combine code and tests
            full_response = f"{generated_code}\n\n# Tests\n{tests}" if tests else generated_code
            
            return full_response
            
        except Exception as e:
            self.logger.error(f"Day_07 agent generation failed: {e}")
            raise
    
    async def _generate_with_fallback(
        self,
        query: str,
        model_name: str,
        max_tokens: int
    ) -> str:
        """Fallback code generation using direct model client."""
        try:
            # Create a simple prompt for code generation
            prompt = f"""Write Python code for the following task:

{query}

Requirements:
- Include proper docstrings
- Add type hints
- Follow PEP8 style
- Include error handling
- Provide example usage

Code:"""
            
            response = await self.model_client.make_request(
                model_name=model_name,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.response
            
        except Exception as e:
            self.logger.error(f"Fallback generation failed: {e}")
            raise
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics from the underlying generator agent."""
        if self.generator_agent:
            return {
                "agent_type": "CodeGeneratorAgent",
                "model_name": self.generator_agent.model_name,
                "total_requests": self.generator_agent.stats["total_requests"],
                "successful_requests": self.generator_agent.stats["successful_requests"],
                "failed_requests": self.generator_agent.stats["failed_requests"],
                "total_tokens_used": self.generator_agent.stats["total_tokens_used"],
                "average_response_time": self.generator_agent.get_average_response_time(),
                "uptime": self.generator_agent.get_uptime()
            }
        else:
            return {
                "agent_type": "FallbackGenerator",
                "status": "day_07 agent not available"
            }
