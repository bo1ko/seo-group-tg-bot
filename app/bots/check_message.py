import asyncio
import re

from aiogram.types import Message
from dotenv import load_dotenv
from pyrogram import Client
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.orm_query import orm_get_users, orm_get_keywords

load_dotenv()


class CheckMessage:
    def __init__(self, message: Message):
        self.client = Client('sessions/my_account')
        self.keywords = None
        self.message = message
        self.users = None
        self.user_ids = None
        self.is_client_started = False

    async def start(self):
        if not self.is_client_started:
            await self.client.start()
            print('Start')
            self.is_client_started = True

    async def stop(self):
        if self.is_client_started:
            await self.client.stop()
            print('Stop')
            self.is_client_started = False

    async def send_message_to_all_users(self, text: str):
        for user_id in self.user_ids:
            await self.message.bot.send_message(user_id, text)

    def contains_keywords(self, text: str) -> bool:
        text = text.lower()
        for keyword in self.keywords:
            keyword = keyword.lower()
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                return True
        return False

    async def check_chat(self, session: AsyncSession):
        try:
            await self.start()
            self.users = await orm_get_users(session)
            self.user_ids = [user.tg_id for user in self.users]
            keywords_objs = await orm_get_keywords(session)
            self.keywords = [i.word for i in keywords_objs]

            while True:
                async for dialog in self.client.get_dialogs():
                    if dialog.unread_messages_count > 0:
                        async for chat_message in self.client.get_chat_history(dialog.chat.id,
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

                                await self.send_message_to_all_users(info_message)
                        await self.client.read_chat_history(dialog.chat.id)
                await asyncio.sleep(5)
        except Exception as e:
            await self.send_message_to_all_users(f"{e}")
        finally:
            await self.stop()
