from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, FloodWait, PhoneCodeInvalid, PhoneCodeExpired

import app.database.orm_query as rq
import app.keyboards.admin_keyboard as kb


class TelegramLogin:
    def __init__(self):
        self.api_id = None
        self.api_hash = None
        self.phone_number = None
        self.phone_code_hash = None
        self.app = None
        self.session = None

    async def pyrogram_login(self, message: Message, state: FSMContext):
        user_data = await state.get_data()
        phone_number = user_data.get("phone_number")

        orm_data = await rq.orm_get_account(phone_number)

        self.phone_number = phone_number
        self.api_id = orm_data.api_id
        self.api_hash = orm_data.api_hash

        if self.app is None:
            self.app = Client(f"sessions/{phone_number}", api_id=self.api_id, api_hash=self.api_hash)

        if not self.app.is_connected:
            await self.app.connect()

        try:
            code = await self.app.send_code(phone_number)
            self.phone_code_hash = code.phone_code_hash

            await message.answer(f"Введи код підтвердження, який отримав на {phone_number}")
        except Exception as e:
            await message.answer(f"Не вдалося надіслати код: {str(e)}")
            await rq.orm_remove_account(phone_number)

    # Second step - code
    async def finish_login(self, message, code_text):
        if not self.phone_number or not self.phone_code_hash:
            await message.answer("Немає збережених даних для авторизації.")
            return

        try:
            await self.app.sign_in(self.phone_number, self.phone_code_hash, code_text)
            await message.answer("Авторизація успішна!", reply_markup=kb.admin_menu)
        except SessionPasswordNeeded:
            await message.answer("Потрібен пароль для двоетапної авторизації. Введи пароль.",
                                 reply_markup=kb.admin_menu)
            await rq.orm_remove_account(self.phone_number)
        except PhoneCodeInvalid:
            await message.answer("Неправильний код підтвердження. Спробуй ще раз.", reply_markup=kb.admin_menu)
            await rq.orm_remove_account(self.phone_number)
        except PhoneCodeExpired:
            await message.answer("Код підтвердження закінчився. Спробуй отримати новий код.",
                                 reply_markup=kb.admin_menu)
            await rq.orm_remove_account(self.phone_number)
        except FloodWait as e:
            await message.answer(f"Тимчасове блокування. Будь ласка, зачекай {e.value} секунд.",
                                 reply_markup=kb.admin_menu)
            await rq.orm_remove_account(self.phone_number)
        except Exception as e:
            await message.answer(f"Помилка авторизації: {str(e)}", reply_markup=kb.admin_menu)
            await rq.orm_remove_account(self.phone_number)
        finally:
            await self.app.disconnect()
