"""Experiment run entity with identity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from src.domain.entities.agent_task import AgentTask


class ExperimentStatus(str, Enum):
    """Experiment status enum."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExperimentRun:
    """
    Domain entity representing an experiment run.

    Attributes:
        experiment_id: Unique identifier for experiment
        experiment_name: Name of the experiment
        status: Current status of experiment
        agent_tasks: List of tasks in the experiment
        model_config_id: Configuration used for experiment
        created_at: Experiment creation timestamp
        updated_at: Last update timestamp
        metadata: Optional additional metadata
    """

    experiment_id: str
    experiment_name: str
    status: ExperimentStatus
    agent_tasks: List[AgentTask] = field(default_factory=list)
    model_config_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)

    def add_task(self, task: AgentTask) -> None:
        """
        Add task to experiment.

        Args:
            task: Task to add
        """
        self.agent_tasks.append(task)
        self.updated_at = datetime.utcnow()

    def start(self) -> None:
        """Start experiment."""
        self.status = ExperimentStatus.RUNNING
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """Mark experiment as completed."""
        self.status = ExperimentStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def fail(self) -> None:
        """Mark experiment as failed."""
        self.status = ExperimentStatus.FAILED
        self.updated_at = datetime.utcnow()

    def add_metadata(self, key: str, value: str) -> None:
        """
        Add metadata to experiment.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()

    def get_total_tokens(self) -> int:
        """
        Calculate total tokens used in experiment.

        Returns:
            Total number of tokens used
        """
        total = 0
        for task in self.agent_tasks:
            if task.token_info and task.token_info.token_count:
                total += task.token_info.token_count.total_tokens
        return total

    def get_task_count(self) -> int:
        """
        Get number of tasks in experiment.

        Returns:
            Number of tasks
        """
        return len(self.agent_tasks)
