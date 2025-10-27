"""Agent task entity with identity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from src.domain.value_objects.compression_result import CompressionResult
from src.domain.value_objects.quality_metrics import Metrics
from src.domain.value_objects.token_info import TokenInfo


class TaskStatus(str, Enum):
    """Agent task status enum."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Agent task type enum."""

    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CODE_ANALYSIS = "code_analysis"
    TOKEN_ANALYSIS = "token_analysis"


@dataclass
class AgentTask:
    """
    Domain entity representing an agent task.

    Attributes:
        task_id: Unique identifier for the task
        task_type: Type of the task
        status: Current status of the task
        prompt: Task prompt or input
        response: Task response or output
        agent_name: Name of the agent handling the task
        model_config_id: Identifier of the model configuration
        token_info: Token usage information
        quality_metrics: Quality metrics
        compression_result: Compression result if applicable
        created_at: Task creation timestamp
        updated_at: Last update timestamp
        metadata: Optional additional metadata
    """

    task_id: str
    task_type: TaskType
    status: TaskStatus
    prompt: str
    response: Optional[str] = None
    agent_name: str = ""
    model_config_id: Optional[str] = None
    token_info: Optional[TokenInfo] = None
    quality_metrics: Optional[Metrics] = None
    compression_result: Optional[CompressionResult] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)

    def mark_in_progress(self) -> None:
        """Mark task as in progress."""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()

    def mark_completed(self, response: str) -> None:
        """
        Mark task as completed with response.

        Args:
            response: Task response
        """
        self.status = TaskStatus.COMPLETED
        self.response = response
        self.updated_at = datetime.utcnow()

    def mark_failed(self) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.updated_at = datetime.utcnow()

    def update_response(self, response: str) -> None:
        """
        Update task response.

        Args:
            response: Updated response
        """
        self.response = response
        self.updated_at = datetime.utcnow()

    def add_metadata(self, key: str, value: str) -> None:
        """
        Add metadata to task.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()

    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if task has failed."""
        return self.status == TaskStatus.FAILED
