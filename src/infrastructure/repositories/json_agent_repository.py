"""JSON-based agent repository implementation."""

import json
from pathlib import Path
from typing import List, Optional

from src.domain.entities.agent_task import AgentTask, TaskStatus, TaskType
from src.domain.repositories.agent_repository import AgentRepository


class JsonAgentRepository(AgentRepository):
    """JSON file-based agent repository."""

    def __init__(self, storage_path: Path) -> None:
        """
        Initialize repository.

        Args:
            storage_path: Path to JSON storage file
        """
        self.storage_path = storage_path
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory and file exist."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text("{}")

    async def save(self, task: AgentTask) -> None:
        """
        Save or update agent task.

        Args:
            task: Agent task entity
        """
        data = self._load_data()
        data[task.task_id] = self._serialize_task(task)
        self._save_data(data)

    async def get_by_id(self, task_id: str) -> Optional[AgentTask]:
        """
        Get agent task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Agent task entity or None
        """
        data = self._load_data()
        task_data = data.get(task_id)
        if not task_data:
            return None
        return self._deserialize_task(task_data)

    async def get_all(self) -> List[AgentTask]:
        """
        Get all agent tasks.

        Returns:
            List of agent task entities
        """
        data = self._load_data()
        return [self._deserialize_task(task_data) for task_data in data.values()]

    async def delete(self, task_id: str) -> bool:
        """
        Delete agent task.

        Args:
            task_id: Task identifier

        Returns:
            True if deleted, False if not found
        """
        data = self._load_data()
        if task_id not in data:
            return False
        del data[task_id]
        self._save_data(data)
        return True

    async def exists(self, task_id: str) -> bool:
        """
        Check if task exists.

        Args:
            task_id: Task identifier

        Returns:
            True if exists, False otherwise
        """
        data = self._load_data()
        return task_id in data

    def _load_data(self) -> dict:
        """Load data from JSON file."""
        if not self.storage_path.exists():
            return {}
        content = self.storage_path.read_text()
        if not content.strip():
            return {}
        return json.loads(content)

    def _save_data(self, data: dict) -> None:
        """Save data to JSON file."""
        self.storage_path.write_text(json.dumps(data, indent=2, default=str))

    def _serialize_task(self, task: AgentTask) -> dict:
        """Serialize task to dictionary."""
        return {
            "task_id": task.task_id,
            "task_type": task.task_type.value,
            "status": task.status.value,
            "prompt": task.prompt,
            "response": task.response,
            "agent_name": task.agent_name,
            "model_config_id": task.model_config_id,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "metadata": task.metadata,
        }

    def _deserialize_task(self, data: dict) -> AgentTask:
        """Deserialize task from dictionary."""
        from datetime import datetime

        return AgentTask(
            task_id=data["task_id"],
            task_type=TaskType(data["task_type"]),
            status=TaskStatus(data["status"]),
            prompt=data["prompt"],
            response=data.get("response"),
            agent_name=data.get("agent_name", ""),
            model_config_id=data.get("model_config_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
        )
