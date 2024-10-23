import time

from aiogram.types import Message
from pyrogram import Client
from pyrogram.errors import FloodWait, ChannelPrivate, UsernameInvalid, InviteRequestSent, UsernameNotOccupied

from app.database.orm_query import orm_channel_processed, orm_add_channel
from app.utils.helpers import load_excel_data, random_sleep


class ChatJoiner:
    def __init__(self, message: Message):
        self.client = Client("sessions/my_account")
        self.message: Message = message
        self.data = load_excel_data()

    async def start(self):
        await self.client.start()

    async def join_chats(self):
        await self.start()
        for item in self.data[1:]:
            chat = item[0].split("/")[-1]

            if orm_channel_processed(chat):
                await self.message.answer(f"Канал {chat} вже був оброблений, пропускаємо.")
                continue

            try:
                await self.client.join_chat(chat)
                await self.message.answer(f"Успішно приєдналися до {chat}")
                orm_add_channel(chat, True)
                random_sleep()
            except InviteRequestSent:
                await self.message.answer(f"Запит на приєднання до {chat} вже надісланий. Чекаємо на схвалення.")
                orm_add_channel(chat, True)
            except ChannelPrivate:
                await self.message.answer(f"Не вдалося приєднатися до {chat}: канал приватний.")
                orm_add_channel(chat, False)
            except UsernameInvalid:
                await self.message.answer(f"Неправильний або недійсний {item[0]}")
                orm_add_channel(chat, False)
            except UsernameNotOccupied:
                await self.message.answer(f"Канал з назвою {item[0]} не існує або він видалений.")
                orm_add_channel(chat, False)
            except FloodWait as e:
                await self.message.answer(f"FloodWait: необхідно зачекати {e.value} секунд")
                time.sleep(e.value)
            except Exception as e:
                await self.message.answer(f'Error: {e}\n\n{chat}')
                orm_add_channel(chat, False)
