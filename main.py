from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError

from config import get_settings
from database import Database
from handlers import setup_handlers


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    database = Database(settings.database_path)
    bot = Bot(token=settings.telegram_bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(setup_handlers(database))

    @dispatcher.errors()
    async def on_error(event: object) -> bool:
        logger.exception("Error no controlado por el dispatcher: %s", event)
        return True

    try:
        logger.info("Bot iniciado. Esperando mensajes...")
        await dispatcher.start_polling(bot)
    except TelegramAPIError:
        logger.exception("Error de Telegram API.")
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
