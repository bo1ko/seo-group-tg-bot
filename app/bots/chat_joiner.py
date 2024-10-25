import asyncio

from aiogram.types import Message
from pyrogram import Client
from pyrogram.errors import FloodWait, ChannelPrivate, UsernameInvalid, InviteRequestSent, UsernameNotOccupied

from app.database.orm_query import orm_channel_processed, orm_add_channel, orm_get_users, orm_set_account_active, \
    orm_update_active_type
from app.utils.helpers import load_excel_data, random_sleep


class ChatJoiner:
    def __init__(self, phone_number: str, message: Message):
        self.client = Client(f"sessions/{phone_number}")
        self.phone_number = phone_number
        self.message: Message = message
        self.data = load_excel_data()
        self.users = None
        self.user_ids = None

    async def start(self):
        await self.client.start()

    async def stop(self):
        await self.client.stop()

    async def send_message_to_all_users(self, text: str):
        for user_id in self.user_ids:
            await self.message.bot.send_message(user_id, text)

    async def join_chats(self):
        try:
            await orm_set_account_active(self.phone_number, True)
            await orm_update_active_type(self.phone_number, 'group')
            await self.start()
            self.users = await orm_get_users()
            self.user_ids = [user.tg_id for user in self.users]

            for item in self.data[1:]:
                chat = item[0].split("/")[-1]

                if await orm_channel_processed(chat):
                    continue

                try:
                    await self.client.join_chat(chat)
                    await orm_add_channel(chat, self.phone_number, True)
                    await random_sleep()
                except InviteRequestSent:
                    await self.send_message_to_all_users(f"Запит на приєднання до {chat} вже надісланий. Чекаємо на схвалення.")
                    await orm_add_channel(chat, self.phone_number, True)
                except ChannelPrivate:
                    await self.send_message_to_all_users(f"Не вдалося приєднатися до {chat}: канал приватний.")
                    await orm_add_channel(chat, self.phone_number, False)
                except UsernameInvalid:
                    await self.send_message_to_all_users(f"Неправильний або недійсний {item[0]}")
                    await orm_add_channel(chat, self.phone_number, False)
                except UsernameNotOccupied:
                    await self.send_message_to_all_users(f"Канал з назвою {item[0]} не існує або він видалений.")
                    await orm_add_channel(chat, self.phone_number, False)
                except FloodWait as e:
                    await self.send_message_to_all_users(f"FloodWait: необхідно зачекати {e.value} секунд")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    await self.send_message_to_all_users(f'Error: {e}\n\n{chat}')
                    await orm_add_channel(chat, self.phone_number, False)
        finally:
            await orm_update_active_type(self.phone_number, '')
            await orm_set_account_active(self.phone_number, False)
            await self.stop()
