"""
Repository interfaces for the token analysis domain.

This module defines the repository interfaces that abstract data access
for domain entities, following the Repository pattern.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..entities.token_analysis_entities import (
    CompressionJob,
    ExperimentSession,
    TokenAnalysisDomain,
)


class TokenAnalysisRepository(ABC):
    """
    Repository interface for TokenAnalysisDomain entities.

    This interface defines the contract for persisting and retrieving
    token analysis entities without exposing implementation details.
    """

    @abstractmethod
    async def save(self, analysis: TokenAnalysisDomain) -> None:
        """
        Save a token analysis entity.

        Args:
            analysis: Token analysis entity to save
        """
        pass

    @abstractmethod
    async def find_by_id(self, analysis_id: str) -> Optional[TokenAnalysisDomain]:
        """
        Find token analysis by ID.

        Args:
            analysis_id: Analysis identifier

        Returns:
            Optional[TokenAnalysisDomain]: Found analysis or None
        """
        pass

    @abstractmethod
    async def find_by_model(
        self, model_name: str, model_version: str
    ) -> List[TokenAnalysisDomain]:
        """
        Find analyses by model.

        Args:
            model_name: Model name
            model_version: Model version

        Returns:
            List[TokenAnalysisDomain]: List of analyses
        """
        pass

    @abstractmethod
    async def find_by_status(self, status: str) -> List[TokenAnalysisDomain]:
        """
        Find analyses by status.

        Args:
            status: Analysis status

        Returns:
            List[TokenAnalysisDomain]: List of analyses
        """
        pass

    @abstractmethod
    async def find_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[TokenAnalysisDomain]:
        """
        Find analyses by date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List[TokenAnalysisDomain]: List of analyses
        """
        pass

    @abstractmethod
    async def find_completed_analyses(self) -> List[TokenAnalysisDomain]:
        """
        Find all completed analyses.

        Returns:
            List[TokenAnalysisDomain]: List of completed analyses
        """
        pass

    @abstractmethod
    async def find_failed_analyses(self) -> List[TokenAnalysisDomain]:
        """
        Find all failed analyses.

        Returns:
            List[TokenAnalysisDomain]: List of failed analyses
        """
        pass

    @abstractmethod
    async def count_by_model(self, model_name: str) -> int:
        """
        Count analyses by model.

        Args:
            model_name: Model name

        Returns:
            int: Number of analyses
        """
        pass

    @abstractmethod
    async def delete(self, analysis_id: str) -> bool:
        """
        Delete analysis by ID.

        Args:
            analysis_id: Analysis identifier

        Returns:
            bool: True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, analysis_id: str) -> bool:
        """
        Check if analysis exists.

        Args:
            analysis_id: Analysis identifier

        Returns:
            bool: True if exists, False otherwise
        """
        pass


class CompressionJobRepository(ABC):
    """
    Repository interface for CompressionJob entities.

    This interface defines the contract for persisting and retrieving
    compression job entities.
    """

    @abstractmethod
    async def save(self, job: CompressionJob) -> None:
        """
        Save a compression job entity.

        Args:
            job: Compression job entity to save
        """
        pass

    @abstractmethod
    async def find_by_id(self, job_id: str) -> Optional[CompressionJob]:
        """
        Find compression job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Optional[CompressionJob]: Found job or None
        """
        pass

    @abstractmethod
    async def find_by_status(self, status: str) -> List[CompressionJob]:
        """
        Find jobs by status.

        Args:
            status: Job status

        Returns:
            List[CompressionJob]: List of jobs
        """
        pass

    @abstractmethod
    async def find_by_priority(self, priority: int) -> List[CompressionJob]:
        """
        Find jobs by priority.

        Args:
            priority: Job priority

        Returns:
            List[CompressionJob]: List of jobs
        """
        pass

    @abstractmethod
    async def find_queued_jobs(self) -> List[CompressionJob]:
        """
        Find all queued jobs.

        Returns:
            List[CompressionJob]: List of queued jobs
        """
        pass

    @abstractmethod
    async def find_retryable_jobs(self) -> List[CompressionJob]:
        """
        Find jobs that can be retried.

        Returns:
            List[CompressionJob]: List of retryable jobs
        """
        pass

    @abstractmethod
    async def find_completed_jobs(self) -> List[CompressionJob]:
        """
        Find all completed jobs.

        Returns:
            List[CompressionJob]: List of completed jobs
        """
        pass

    @abstractmethod
    async def delete(self, job_id: str) -> bool:
        """
        Delete job by ID.

        Args:
            job_id: Job identifier

        Returns:
            bool: True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def count_by_status(self, status: str) -> int:
        """
        Count jobs by status.

        Args:
            status: Job status

        Returns:
            int: Number of jobs
        """
        pass


class ExperimentSessionRepository(ABC):
    """
    Repository interface for ExperimentSession entities.

    This interface defines the contract for persisting and retrieving
    experiment session entities.
    """

    @abstractmethod
    async def save(self, session: ExperimentSession) -> None:
        """
        Save an experiment session entity.

        Args:
            session: Experiment session entity to save
        """
        pass

    @abstractmethod
    async def find_by_id(self, session_id: str) -> Optional[ExperimentSession]:
        """
        Find experiment session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Optional[ExperimentSession]: Found session or None
        """
        pass

    @abstractmethod
    async def find_by_experiment_name(
        self, experiment_name: str
    ) -> List[ExperimentSession]:
        """
        Find sessions by experiment name.

        Args:
            experiment_name: Experiment name

        Returns:
            List[ExperimentSession]: List of sessions
        """
        pass

    @abstractmethod
    async def find_by_model(self, model_name: str) -> List[ExperimentSession]:
        """
        Find sessions by model.

        Args:
            model_name: Model name

        Returns:
            List[ExperimentSession]: List of sessions
        """
        pass

    @abstractmethod
    async def find_by_status(self, status: str) -> List[ExperimentSession]:
        """
        Find sessions by status.

        Args:
            status: Session status

        Returns:
            List[ExperimentSession]: List of sessions
        """
        pass

    @abstractmethod
    async def find_completed_sessions(self) -> List[ExperimentSession]:
        """
        Find all completed sessions.

        Returns:
            List[ExperimentSession]: List of completed sessions
        """
        pass

    @abstractmethod
    async def find_running_sessions(self) -> List[ExperimentSession]:
        """
        Find all running sessions.

        Returns:
            List[ExperimentSession]: List of running sessions
        """
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """
        Delete session by ID.

        Args:
            session_id: Session identifier

        Returns:
            bool: True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def count_by_experiment(self, experiment_name: str) -> int:
        """
        Count sessions by experiment.

        Args:
            experiment_name: Experiment name

        Returns:
            int: Number of sessions
        """
        pass


class MetricsRepository(ABC):
    """
    Repository interface for metrics and analytics data.

    This interface defines the contract for persisting and retrieving
    metrics and analytics data.
    """

    @abstractmethod
    async def save_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Save metrics data.

        Args:
            metrics: Metrics data to save
        """
        pass

    @abstractmethod
    async def get_model_performance(self, model_name: str) -> Dict[str, Any]:
        """
        Get performance metrics for a model.

        Args:
            model_name: Model name

        Returns:
            Dict[str, Any]: Performance metrics
        """
        pass

    @abstractmethod
    async def get_experiment_metrics(self, experiment_name: str) -> Dict[str, Any]:
        """
        Get metrics for an experiment.

        Args:
            experiment_name: Experiment name

        Returns:
            Dict[str, Any]: Experiment metrics
        """
        pass

    @abstractmethod
    async def get_aggregated_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dict[str, Any]: Aggregated metrics
        """
        pass

    @abstractmethod
    async def get_top_performing_models(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing models.

        Args:
            limit: Maximum number of models to return

        Returns:
            List[Dict[str, Any]]: List of top performing models
        """
        pass

    @abstractmethod
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get overall metrics summary.

        Returns:
            Dict[str, Any]: Metrics summary
        """
        pass
