import asyncio
import re
import sys

from aiogram.types import Message
from dotenv import load_dotenv
from pyrogram import Client

from app.database.orm_query import (
    orm_get_users,
    orm_get_accounts,
    orm_set_account_active,
    orm_get_subscribers,
)

load_dotenv()


class CheckMessage:
    def __init__(self, message: Message):
        self.message = message
        self.is_client_started = False

    async def start(self, client):
        if not self.is_client_started:
            await client.start()
            self.is_client_started = True

    async def stop(self, client):
        if self.is_client_started:
            await client.stop()
            self.is_client_started = False

    async def contains_keywords(self, text: str, users_key_words: dict, info_message: str) -> bool:
        text = text.lower()

        for item, kw_list in users_key_words.items():
            has_kw = False
            
            for value in kw_list:
                keyword = value.lower()
                pattern = r"\b" + re.escape(keyword) + r"\b"

                if re.search(pattern, text):
                    has_kw = True
            
            if has_kw:
                await self.message.bot.send_message(item, info_message)

        return False

    async def check_chat(self):
        last_exception = ""

        try:
            while True:
                users = await orm_get_users()
                subs = await orm_get_subscribers()
                sub_ids = []
                
                users_key_words = {}
                admins = []
                
                for sub in subs:
                    if sub.is_subscribed:
                        sub_ids.append(sub.user_id)

                for user in users:
                    if user.tg_id in sub_ids:
                        users_key_words[int(user.tg_id)] = user.key_list
                        
                    if user.is_admin:
                        admins.append(int(user.tg_id))

                accounts = await orm_get_accounts()

                for account in accounts:
                    if not account.is_active:
                        await orm_set_account_active(account.phone_number, True)
                        client = Client(f"sessions/{account.phone_number}")

                        try:
                            await self.start(client)
                            async for dialog in client.get_dialogs():
                                if dialog.unread_messages_count > 0:
                                    async for chat_message in client.get_chat_history(
                                        dialog.chat.id,
                                        limit=dialog.unread_messages_count,
                                    ):
                                        if chat_message.text:
                                            chat_link = (
                                                f"https://t.me/{chat_message.chat.username}"
                                                if chat_message.chat.username
                                                else "Посилання відсутнє"
                                            )
                                            message_link = (
                                                f"https://t.me/{chat_message.chat.username}/{chat_message.id}"
                                                if chat_message.chat.username
                                                else "Посилання відсутнє"
                                            )

                                            info_message = (
                                                f"Чат: {chat_message.chat.title}\n"
                                                f"Посилання на чат: {chat_link}\n"
                                                f"Посилання на повідомлення: {message_link}\n"
                                                f"Автор: {chat_message.from_user.username or chat_message.from_user.first_name}\n"
                                                f"Текст: {chat_message.text}"
                                            )

                                            await self.contains_keywords(
                                                chat_message.text, users_key_words, info_message
                                            )
                                    await client.read_chat_history(dialog.chat.id)
                            await self.stop(client)
                            await asyncio.sleep(5)
                        except Exception as e:
                            if last_exception != e:
                                for admin in admins:
                                    last_exception = e
                                    await self.message.answer(admin, f"{e}")
                        finally:
                            await orm_set_account_active(account.phone_number, False)
                            await self.stop(client)

                        await asyncio.sleep(60)
        except Exception as e:
            self.message.bot.send_message(chat_id=1029023222, text=f'ПРОЦЕС ПРОВІРКИ ЧАТІВ ERROR\n{e}')