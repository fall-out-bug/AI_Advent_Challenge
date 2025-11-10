"""Bot handlers package."""

from src.presentation.bot.handlers.base import Handler
from src.presentation.bot.handlers.chat import ChatHandler
from src.presentation.bot.handlers.data import DataHandler
from src.presentation.bot.handlers.homework import HomeworkHandler
from src.presentation.bot.handlers.task import TaskHandler

__all__ = [
    "Handler",
    "ChatHandler",
    "DataHandler",
    "HomeworkHandler",
    "TaskHandler",
]
