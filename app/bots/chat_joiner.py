import asyncio
import os
import traceback
import logging

from datetime import datetime, timedelta
from aiogram.types import Message, FSInputFile
from pyrogram import Client
from pyrogram.errors import (
    FloodWait,
    ChannelPrivate,
    UsernameInvalid,
    InviteRequestSent,
    UsernameNotOccupied,
    PeerFlood,
    RPCError,
    BadRequest,
)
from dotenv import load_dotenv

from app.database.orm_query import (
    orm_channel_processed,
    orm_add_channel,
    orm_get_users,
    orm_set_account_active,
    orm_get_accounts,
    orm_update_flood_wait,
)
from app.utils.helpers import load_excel_data, random_sleep

logger = logging.getLogger(__name__)
load_dotenv()


class ChatJoiner:
    def __init__(self, message: Message):
        self.message: Message = message
        self.data, self.count = load_excel_data()
        self.users = None

    log_file_path = "channel_log.txt"

    async def start(self, client: Client):
        await client.start()

    async def stop(self, client: Client):
        await client.stop()

    async def send_message_to_all_admins(self, text: str):
        for user in self.users:
            if user.is_admin:
                await self.message.bot.send_message(user.tg_id, text)

    async def log_channel_status(self, chat_url, success=True, text=""):
        status = "Успішно додано" if success else "Неуспішно додано"
        with open(self.log_file_path, "a", encoding="utf-8") as file:
            file.write(f"{status}: {chat_url} - {text}\n")

    async def join_chats(self, country: str, city: str, is_general: bool):
        try:
            accounts = await orm_get_accounts()
            account_index = 0

            for i, item in enumerate(self.data):
                if i >= self.count:
                    break

                account = accounts[account_index]
                phone_number = account.phone_number

                if not phone_number:
                    logger.warning("Номер телефону не знайдено для акаунта.")
                    continue

                # Перевірка flood wait
                if account.flood_wait:
                    if account.flood_wait > datetime.now():
                        logger.info(f"{phone_number} все ще перебуває у flood wait.")
                        continue
                
                await asyncio.sleep(20)

                client = Client(f"sessions/{phone_number}")
                await orm_set_account_active(phone_number, True)

                try:
                    await self.start(client)
                    chat = item[0].split("/")[-1]
                    channel_processed, channel_processed_phone_number = await orm_channel_processed(chat)

                    if channel_processed:
                        logger.info(f"Канал {chat} вже оброблений.")
                        await self.log_channel_status(chat, success=False, text="Вже оброблено")
                        continue

                    try:
                        await client.join_chat(chat)
                        await orm_add_channel(chat, phone_number, True, country, city, is_general)
                        logger.info(f"Канал {chat} успішно доданий.")
                        await self.log_channel_status(chat, success=True)
                    except InviteRequestSent:
                        logger.warning(f"Запит на приєднання до {chat} вже надісланий.")
                        await self.log_channel_status(chat, success=False, text="Запит вже надісланий")
                    except ChannelPrivate:
                        logger.warning(f"Канал {chat} приватний.")
                        await self.log_channel_status(chat, success=False, text="Канал приватний")
                    except UsernameInvalid:
                        logger.warning(f"Неправильний {chat}.")
                        await self.log_channel_status(chat, success=False, text="Неправильний username")
                    except UsernameNotOccupied:
                        logger.warning(f"Канал {chat} не існує.")
                        await self.log_channel_status(chat, success=False, text="Канал не існує")
                    except FloodWait as e:
                        account_index = (account_index + 1) % len(accounts)
                        wait_until = datetime.now() + timedelta(seconds=e.value)
                        logger.warning(f"FloodWait: необхідно зачекати {e.value} секунд.")
                        await orm_update_flood_wait(phone_number, wait_until)
                        await self.message.answer(f"Номер {phone_number} - flod {e.value}")
                        continue
                    except PeerFlood:
                        account_index = (account_index + 1) % len(accounts)
                        logger.error(f"{phone_number} отримав PeerFlood.")
                        await self.log_channel_status(chat, success=False, text="PeerFlood")
                        await self.message.answer(f"Номер {phone_number} - PeerFlood {e.value}")
                        continue
                    except BadRequest as e:
                        logger.error(f"BadRequest: {e}.")
                        await self.log_channel_status(chat, success=False, text=f"BadRequest: {e}")
                    except RPCError as e:
                        logger.error(f"RPCError: {e}.")
                        await self.log_channel_status(chat, success=False, text=f"RPCError: {e}")
                    except Exception as e:
                        error_message = traceback.format_exc()
                        logger.error(f"Невідома помилка: {e}\n{error_message}")
                        await self.log_channel_status(chat, success=False, text=f"Невідома помилка: {e}")
                finally:
                    await orm_set_account_active(phone_number, False)
                    await self.stop(client)

                # Перехід до наступного акаунта
                account_index = (account_index + 1) % len(accounts)

        finally:
            await self.message.answer("Додавання чатів завершено.")
            
            if os.path.getsize(self.log_file_path) > 0:
                info_file = FSInputFile(self.log_file_path, filename="result.txt")
                await self.message.bot.send_document(chat_id=self.message.chat.id, document=info_file)

            with open(self.log_file_path, "w", encoding="utf-8") as file:
                file.write("")
