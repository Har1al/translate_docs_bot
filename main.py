import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config.config import Config, load_config
from handlers.user import user_router
from handlers.other import other_router

logger = logging.getLogger(__name__)

async def main():
    config = load_config()

    logging.basicConfig(
        format=config.log.format,
        level=logging.getLevelName(level=config.log.level)
    )

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()

    dp.include_router(user_router)
    dp.include_router(other_router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())