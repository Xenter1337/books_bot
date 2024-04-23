import asyncio
import os

from aiogram import Dispatcher, Bot
from dotenv import load_dotenv

from handlers.client import router
from database.core import db


async def main():
    bot = Bot(os.getenv("BOT_TOKEN"))
    dp = Dispatcher()

    # Запуск базы данных
    dp.startup.register(db.startup)
    dp.shutdown.register(db.shutdown)
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
