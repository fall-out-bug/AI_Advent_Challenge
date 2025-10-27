"""Agent data transfer objects."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AgentTaskDTO:
    """
    Data transfer object for agent task.

    Attributes:
        task_id: Task identifier
        task_type: Type of task
        status: Current status
        prompt: Task prompt
        response: Task response
        agent_name: Agent name
        created_at: Creation timestamp
    """

    task_id: str
    task_type: str
    status: str
    prompt: str
    response: Optional[str]
    agent_name: str
    created_at: datetime

    def to_dict(self) -> dict:
        """
        Convert DTO to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status,
            "prompt": self.prompt,
            "response": self.response,
            "agent_name": self.agent_name,
            "created_at": self.created_at.isoformat(),
        }
