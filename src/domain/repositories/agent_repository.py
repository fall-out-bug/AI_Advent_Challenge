"""Agent repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.agent_task import AgentTask


class AgentRepository(ABC):
    """Abstract repository for agent tasks."""

    @abstractmethod
    async def save(self, task: AgentTask) -> None:
        """
        Save or update an agent task.

        Args:
            task: Agent task entity
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, task_id: str) -> Optional[AgentTask]:
        """
        Get agent task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Agent task entity or None if not found
        """
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[AgentTask]:
        """
        Get all agent tasks.

        Returns:
            List of agent task entities
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, task_id: str) -> bool:
        """
        Delete an agent task.

        Args:
            task_id: Task identifier

        Returns:
            True if deleted, False if not found
        """
        raise NotImplementedError

    @abstractmethod
    async def exists(self, task_id: str) -> bool:
        """
        Check if task exists.

        Args:
            task_id: Task identifier

        Returns:
            True if exists, False otherwise
        """
        raise NotImplementedError
