import asyncio
import re

from aiogram.types import Message
from dotenv import load_dotenv
from pyrogram import Client

from app.database.orm_query import orm_get_users, orm_get_keywords, orm_get_accounts, orm_set_account_active, orm_update_active_type

load_dotenv()


class CheckMessage:
    def __init__(self, message: Message):
        self.keywords = None
        self.message = message
        self.users = None
        self.is_client_started = False

    async def start(self, client):
        if not self.is_client_started:
            await client.start()
            self.is_client_started = True

    async def stop(self, client):
        if self.is_client_started:
            await client.stop()
            self.is_client_started = False

    async def send_message_to_all_users(self, text: str, user_ids: list):
        for user_id in user_ids:
            await self.message.bot.send_message(user_id, text)

    def contains_keywords(self, text: str) -> bool:
        text = text.lower()
        for keyword in self.keywords:
            keyword = keyword.lower()
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                return True
        return False

    async def check_chat(self):
        self.users = await orm_get_users()
        user_ids = [user.tg_id for user in self.users]

        keywords_objs = await orm_get_keywords()
        self.keywords = [i.word for i in keywords_objs]

        accounts = await orm_get_accounts()

        for account in accounts:
            await orm_update_active_type(account.phone_number, 'check')
            await orm_set_account_active(account.phone_number, True)

        try:
            if accounts:
                while True:
                    for account in accounts:
                        if not account.is_active:
                            client = Client(f'sessions/{account.phone_number}')
                            try:
                                await self.start(client)
                                async for dialog in client.get_dialogs():
                                    if dialog.unread_messages_count > 0:
                                        async for chat_message in client.get_chat_history(dialog.chat.id,
                                                                                          limit=dialog.unread_messages_count):
                                            if chat_message.text and self.contains_keywords(chat_message.text):
                                                chat_link = f"https://t.me/{chat_message.chat.username}" if chat_message.chat.username else "Посилання відсутнє"
                                                message_link = f"https://t.me/{chat_message.chat.username}/{chat_message.id}" if chat_message.chat.username else "Посилання відсутнє"

                                                info_message = (
                                                    f"Чат: {chat_message.chat.title}\n"
                                                    f"Посилання на чат: {chat_link}\n"
                                                    f"Посилання на повідомлення: {message_link}\n"
                                                    f"Автор: {chat_message.from_user.username or chat_message.from_user.first_name}\n"
                                                    f"Текст: {chat_message.text}"
                                                )

                                                await self.send_message_to_all_users(info_message, user_ids)
                                        await client.read_chat_history(dialog.chat.id)
                                await self.stop(client)
                                await asyncio.sleep(5)
                            except Exception as e:
                                await self.send_message_to_all_users(f"{e}", user_ids)
                            finally:
                                await self.stop(client)

                            await asyncio.sleep(5)
        finally:
            for account in accounts:
                await orm_update_active_type(account.phone_number, '')
                await orm_set_account_active(account.phone_number, False)
