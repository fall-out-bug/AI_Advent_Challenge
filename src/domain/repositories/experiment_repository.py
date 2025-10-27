"""Experiment repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.experiment_run import ExperimentRun


class ExperimentRepository(ABC):
    """Abstract repository for experiment runs."""

    @abstractmethod
    async def save(self, experiment: ExperimentRun) -> None:
        """
        Save or update an experiment run.

        Args:
            experiment: Experiment run entity
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, experiment_id: str) -> Optional[ExperimentRun]:
        """
        Get experiment run by ID.

        Args:
            experiment_id: Experiment identifier

        Returns:
            Experiment run entity or None if not found
        """
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[ExperimentRun]:
        """
        Get all experiment runs.

        Returns:
            List of experiment run entities
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, experiment_id: str) -> bool:
        """
        Delete an experiment run.

        Args:
            experiment_id: Experiment identifier

        Returns:
            True if deleted, False if not found
        """
        raise NotImplementedError
