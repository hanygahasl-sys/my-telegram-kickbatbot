import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

import database
from handlers import router
from tasks import check_deadlines, check_habit_reminders, morning_digest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.critical("BOT_TOKEN не найден в .env файле!")
        return

    bot = Bot(token=token)
    dp = Dispatcher()

    await database.init_db()
    dp.include_router(router)

    asyncio.create_task(check_deadlines(bot))
    asyncio.create_task(morning_digest(bot))
    asyncio.create_task(check_habit_reminders(bot))

    logger.info("Бот запущен.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
