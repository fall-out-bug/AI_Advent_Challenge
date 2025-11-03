"""Use cases for Butler Agent business logic.

Following Clean Architecture: Use cases encapsulate application-specific business rules.
"""

from src.application.usecases.create_task_usecase import CreateTaskUseCase
from src.application.usecases.collect_data_usecase import CollectDataUseCase
from src.application.usecases.result_types import (
    TaskCreationResult,
    DigestResult,
    StatsResult,
)

__all__ = [
    "CreateTaskUseCase",
    "CollectDataUseCase",
    "TaskCreationResult",
    "DigestResult",
    "StatsResult",
]

