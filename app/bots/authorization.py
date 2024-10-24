from aiogram.fsm.context import FSMContext
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, FloodWait, PhoneCodeInvalid, PhoneCodeExpired
import app.keyboards.admin_keyboard as kb

class TelegramLogin:
    def __init__(self, api_id, api_hash):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_code_hash = None
        self.app = None

    async def pyrogram_login(self, message, state: FSMContext):
        if self.app is None:
            self.app = Client("sessions/my_account", api_id=self.api_id, api_hash=self.api_hash)

        if not self.app.is_connected:
            await self.app.connect()

        try:
            user_data = await state.get_data()
            phone_number = user_data.get("phone_number")

            code = await self.app.send_code(phone_number)
            self.phone_code_hash = code.phone_code_hash

            await state.update_data(phone_code_hash=self.phone_code_hash)

            await message.answer(f"Введи код підтвердження, який отримав на {phone_number}")
        except Exception as e:
            await message.answer(f"Не вдалося надіслати код: {str(e)}")

    async def finish_login(self, message, code_text, user_data):
        phone_number = user_data.get("phone_number")
        phone_code_hash = user_data.get("phone_code_hash")

        if not phone_number or not phone_code_hash:
            await message.answer("Немає збережених даних для авторизації.")
            return

        try:
            await self.app.sign_in(phone_number, phone_code_hash, code_text)
            await message.answer("Авторизація успішна!", reply_markup=kb.admin_menu)
        except SessionPasswordNeeded:
            await message.answer("Потрібен пароль для двоетапної авторизації. Введи пароль.", reply_markup=kb.admin_menu)
        except PhoneCodeInvalid:
            await message.answer("Неправильний код підтвердження. Спробуй ще раз.", reply_markup=kb.admin_menu)
        except PhoneCodeExpired:
            await message.answer("Код підтвердження закінчився. Спробуй отримати новий код.", reply_markup=kb.admin_menu)
        except FloodWait as e:
            await message.answer(f"Тимчасове блокування. Будь ласка, зачекай {e.value} секунд.", reply_markup=kb.admin_menu)
        except Exception as e:
            await message.answer(f"Помилка авторизації: {str(e)}", reply_markup=kb.admin_menu)
