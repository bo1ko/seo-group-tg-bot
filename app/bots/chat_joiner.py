import asyncio

from aiogram.types import Message
from pyrogram import Client
from pyrogram.errors import FloodWait, ChannelPrivate, UsernameInvalid, InviteRequestSent, UsernameNotOccupied

from app.database.orm_query import orm_channel_processed, orm_add_channel, orm_get_users
from app.utils.helpers import load_excel_data, random_sleep
from sqlalchemy.ext.asyncio import AsyncSession


class ChatJoiner:
    def __init__(self, message: Message, session: AsyncSession):
        self.client = Client("sessions/my_account")
        self.message: Message = message
        self.data = load_excel_data()
        self.session = session
        self.users = None
        self.user_ids = None

    async def start(self):
        await self.client.start()

    async def stop(self):
        await self.client.stop()

    async def send_message_to_all_users(self, text: str):
        for user_id in self.user_ids:
            await self.message.bot.send_message(user_id, text)

    async def join_chats(self, session: AsyncSession):
        try:
            await self.start()
            self.users = await orm_get_users(session)
            self.user_ids = [user.tg_id for user in self.users]

            for item in self.data[1:]:
                chat = item[0].split("/")[-1]

                if await orm_channel_processed(chat, self.session):
                    continue

                try:
                    await self.client.join_chat(chat)
                    await orm_add_channel(chat, True, self.session)
                    await random_sleep()
                except InviteRequestSent:
                    await self.send_message_to_all_users(f"Запит на приєднання до {chat} вже надісланий. Чекаємо на схвалення.")
                    await orm_add_channel(chat, True, self.session)
                except ChannelPrivate:
                    await self.send_message_to_all_users(f"Не вдалося приєднатися до {chat}: канал приватний.")
                    await orm_add_channel(chat, False, self.session)
                except UsernameInvalid:
                    await self.send_message_to_all_users(f"Неправильний або недійсний {item[0]}")
                    await orm_add_channel(chat, False, self.session)
                except UsernameNotOccupied:
                    await self.send_message_to_all_users(f"Канал з назвою {item[0]} не існує або він видалений.")
                    await orm_add_channel(chat, False, self.session)
                except FloodWait as e:
                    await self.send_message_to_all_users(f"FloodWait: необхідно зачекати {e.value} секунд")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    await self.send_message_to_all_users(f'Error: {e}\n\n{chat}')
                    await orm_add_channel(chat, False, self.session)
        finally:
            await self.stop()
