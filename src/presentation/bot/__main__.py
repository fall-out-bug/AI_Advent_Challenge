"""Bot entrypoint module for Python -m execution."""

import asyncio

from src.presentation.bot.butler_bot import main

if __name__ == "__main__":
    asyncio.run(main())
