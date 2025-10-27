"""Message schemas for agent communication.

Following the Zen of Python:
- Simple is better than complex
- Readability counts
- Explicit is better than implicit
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskMetadata(BaseModel):
    """Metadata about a task.

    Simple data class containing task complexity and dependencies.
    """

    complexity: str = Field(
        default="medium",
        description="Complexity level (low/medium/high)",
    )
    lines_of_code: int = Field(default=0, description="Number of lines in code")
    estimated_time: Optional[str] = Field(None, description="Estimated execution time")
    dependencies: List[str] = Field(
        default_factory=list, description="Required dependencies"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "complexity": self.complexity,
            "lines_of_code": self.lines_of_code,
            "estimated_time": self.estimated_time,
            "dependencies": self.dependencies,
        }


class CodeGenerationRequest(BaseModel):
    """Request for code generation."""

    task_description: str = Field(description="Description of the task to implement")
    language: str = Field(default="python", description="Programming language")
    requirements: List[str] = Field(
        default_factory=list, description="Additional requirements"
    )
    max_tokens: int = Field(default=1000, description="Maximum tokens")
    model_name: str = Field(default="starcoder", description="Model to use")


class CodeGenerationResponse(BaseModel):
    """Response from code generator agent."""

    task_description: str = Field(description="Original task description")
    generated_code: str = Field(description="Generated Python code")
    tests: str = Field(description="Generated unit tests")
    metadata: TaskMetadata = Field(description="Code metadata")
    generation_time: datetime = Field(default_factory=datetime.now)
    tokens_used: int = Field(description="Number of tokens used")


class CodeQualityMetrics(BaseModel):
    """Code quality assessment metrics."""

    pep8_compliance: bool = Field(description="Whether code follows PEP8")
    pep8_score: float = Field(ge=0, le=10, description="PEP8 compliance score (0-10)")
    has_docstrings: bool = Field(description="Whether code has docstrings")
    has_type_hints: bool = Field(description="Whether code has type hints")
    test_coverage: str = Field(description="Test coverage assessment")
    complexity_score: float = Field(ge=0, le=10, description="Code complexity score")


class CodeReviewRequest(BaseModel):
    """Request for code review."""

    task_description: str = Field(description="Original task description")
    generated_code: str = Field(description="Code to review")
    tests: str = Field(description="Tests to review")
    metadata: TaskMetadata = Field(description="Code metadata")


class CodeReviewResponse(BaseModel):
    """Response from code reviewer agent."""

    code_quality_score: float = Field(
        ge=0, le=10, description="Overall code quality score"
    )
    metrics: CodeQualityMetrics = Field(description="Detailed quality metrics")
    issues: List[str] = Field(description="List of identified issues")
    recommendations: List[str] = Field(
        description="List of improvement recommendations"
    )
    review_time: datetime = Field(default_factory=datetime.now)
    tokens_used: int = Field(description="Number of tokens used")


class OrchestratorRequest(BaseModel):
    """Request to orchestrator for full workflow."""

    task_description: str = Field(description="Task to implement")
    language: str = Field(default="python", description="Programming language")
    requirements: List[str] = Field(
        default_factory=list, description="Additional requirements"
    )
    model_name: str = Field(default="starcoder", description="Model for generation")
    reviewer_model_name: Optional[str] = Field(
        None, description="Model for review (defaults to generation model)"
    )


class OrchestratorResponse(BaseModel):
    """Response from orchestrator with complete workflow results."""

    task_description: str = Field(description="Original task description")
    success: bool = Field(description="Whether workflow completed successfully")
    generation_result: Optional[CodeGenerationResponse] = Field(
        None, description="Code generation result"
    )
    review_result: Optional[CodeReviewResponse] = Field(
        None, description="Code review result"
    )
    workflow_time: float = Field(description="Total workflow time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class AgentHealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="Agent status (healthy/unhealthy)")
    agent_type: str = Field(description="Type of agent (generator/reviewer)")
    uptime: float = Field(description="Agent uptime in seconds")
    last_request: Optional[datetime] = Field(None, description="Last request timestamp")


class AgentStatsResponse(BaseModel):
    """Agent statistics response."""

    total_requests: int = Field(description="Total requests processed")
    successful_requests: int = Field(description="Successful requests")
    failed_requests: int = Field(description="Failed requests")
    average_response_time: float = Field(description="Average response time in seconds")
    total_tokens_used: int = Field(description="Total tokens consumed")
