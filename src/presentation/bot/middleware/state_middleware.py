from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class StatePersistenceMiddleware(BaseMiddleware):
    """Persist and load FSM-related context across bot updates.

    Purpose:
        Encapsulates persistence hooks for FSM context, enabling restoring
        partial intents and conversation metadata between updates.

    Args:
        storage: Optional external storage adapter to persist FSM context.
                 If None, relies on aiogram's configured FSM storage.

    Example:
        middleware = StatePersistenceMiddleware()
        dp.update.middleware(middleware)

    Exceptions:
        None
    """

    def __init__(self, storage: Any | None = None) -> None:
        self._storage = storage

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # In a future iteration, enrich `data` with restored context
        # from self._storage (if provided). For now, pass-through.
        return await handler(event, data)
