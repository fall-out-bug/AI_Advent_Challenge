"""
Pydantic schemas for agent communication.

Following Python Zen: "Explicit is better than implicit"
and "Simple is better than complex".
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class TaskMetadata(BaseModel):
    """
    Task metadata for agent execution.
    
    Following Python Zen: "Explicit is better than implicit".
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "task_123",
                "task_type": "code_generation",
                "timestamp": 1234567890.0,
                "model_name": "gpt-4"
            }
        }
    )
    
    task_id: str = Field(..., description="Unique task identifier")
    task_type: str = Field(..., description="Type of task (e.g., 'code_generation', 'code_review')")
    timestamp: float = Field(..., description="Task creation timestamp")
    model_name: Optional[str] = Field(None, description="Model used for execution")


class AgentRequest(BaseModel):
    """
    Standard request format for agents.
    
    Following Python Zen: "Simple is better than complex".
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task": "Generate a function to calculate fibonacci numbers",
                "context": {
                    "language": "python",
                    "style": "functional"
                },
                "metadata": {
                    "task_id": "task_123",
                    "task_type": "code_generation",
                    "timestamp": 1234567890.0,
                    "model_name": "gpt-4"
                }
            }
        }
    )
    
    task: str = Field(..., description="Task description or input")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the task")
    metadata: Optional[TaskMetadata] = Field(None, description="Task metadata")


class QualityMetrics(BaseModel):
    """
    Quality metrics for code review.
    
    Following Python Zen: "Explicit is better than implicit".
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "score": 0.85,
                "readability": 0.9,
                "efficiency": 0.8,
                "correctness": 0.9,
                "maintainability": 0.8,
                "issues_found": 2
            }
        }
    )
    
    score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score (0-1)")
    readability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Readability score")
    efficiency: Optional[float] = Field(None, ge=0.0, le=1.0, description="Efficiency score")
    correctness: Optional[float] = Field(None, ge=0.0, le=1.0, description="Correctness score")
    maintainability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Maintainability score")
    issues_found: int = Field(0, ge=0, description="Number of issues found")


class AgentResponse(BaseModel):
    """
    Standard response format from agents.
    
    Following Python Zen: "Simple is better than complex".
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "result": "def fibonacci(n): ...",
                "success": True,
                "error": None,
                "metadata": {
                    "task_id": "task_123",
                    "task_type": "code_generation",
                    "timestamp": 1234567890.0,
                    "model_name": "gpt-4"
                },
                "quality": None
            }
        }
    )
    
    result: str = Field(..., description="Agent result or output")
    success: bool = Field(..., description="Whether the task was successful")
    error: Optional[str] = Field(None, description="Error message if task failed")
    metadata: Optional[TaskMetadata] = Field(None, description="Task metadata")
    quality: Optional[QualityMetrics] = Field(None, description="Quality metrics (for review tasks)")
