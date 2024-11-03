import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from app.middlewares.db import DataBaseSession
from app.database.engine import session_maker
from app.common.bot_cmds_list import private
from app.database.engine import create_db
from app.database.orm_query import orm_disable_active_accounts
from app.handlers.admin_handler import router as admin_router
from app.handlers.user_handler import router as user_router
from app.handlers.admin_group import router as admin_group_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,  # Рівень логування
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),  # Запис у файл bot.log
        logging.StreamHandler()  # Виведення у консоль
    ]
)

logger = logging.getLogger(__name__)

async def main():
    await create_db()
    await orm_disable_active_accounts()

    bot = Bot(token=os.getenv("BOT_TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()
    dp.include_routers(admin_router, user_router, admin_group_router)
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
