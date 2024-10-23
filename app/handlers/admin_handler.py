import asyncio
import os
import shutil

from aiogram import Router, types, F, Bot
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
from app.bots.authorization import TelegramLogin
from app.bots.chat_joiner import ChatJoiner
from app.database.orm_query import orm_remove_channels

import app.keyboards.admin_keyboard as kb
from app.filters.check_admin import IsAdmin

load_dotenv()

router = Router()
router.message.filter(IsAdmin())
login_manager = TelegramLogin(os.getenv('API_ID'), os.getenv('API_HASH'))


class Auth(StatesGroup):
    waiting_for_phone_number = State()
    waiting_for_code = State()


class ExcelFile(StatesGroup):
    file_name = State()


# admin /admin
@router.message(or_f(Command('admin'), ('Відкрити адмін меню' == F.text), ('Назад' == F.text)))
async def cmd_admin(message: types.Message):
    await message.answer('Hello, admin!', reply_markup=kb.admin_menu)


@router.message(F.text == 'Сховати адмін меню')
async def hide_admin_menu(message: types.Message):
    await message.answer('Адмін меню приховане', reply_markup=kb.hide_admin_menu)


# account
@router.message(F.text == 'Аккаунт')
async def account_manage(message: types.Message):
    if len(os.listdir(os.getenv('SESSION_DIR'))) > 0:
        await message.answer('Виберіть дію', reply_markup=kb.account_manage)
    else:
        await message.answer('Виберіть дію', reply_markup=kb.account_add)


# add account
@router.message(F.text == 'Добавити аккаунт')
async def add_account(message: types.Message, state: FSMContext):
    await message.answer('Введіть номер телефону 👇')
    await state.set_state(Auth.waiting_for_phone_number)


@router.message(Auth.waiting_for_phone_number)
async def phone_number_handler(message: types.Message, state: FSMContext):
    if message.text and message.text.isdigit():
        await state.update_data(phone_number=message.text)
        await message.answer(f"Дякую! Твій номер телефону: {message.text}. Тепер чекай код для входу.")

        asyncio.create_task(login_manager.pyrogram_login(message, state))

        await state.set_state(Auth.waiting_for_code)
    else:
        await message.answer("Введений номер телефону некоректний. Будь ласка, спробуй ще раз.")
        await state.clear()

@router.message(Auth.waiting_for_code)
async def code_handler(message: types.Message, state: FSMContext):
    if message.text and message.text.isdigit():
        user_data = await state.get_data()
        code_text = message.text

        await login_manager.finish_login(message, code_text, user_data)
        await state.clear()
    else:
        await message.answer("Будь ласка, введи коректний код підтвердження.")


# delete account
@router.message(F.text == 'Видалити аккаунт')
async def add_account(message: types.Message, state: FSMContext):
    await message.answer('Аккаунт успішно видалено', reply_markup=kb.admin_menu)
    shutil.rmtree(os.getenv('SESSION'))
    orm_remove_channels()


# add groups
@router.message(F.text == 'Добавити чати')
async def add_groups(message: types.Message, state: FSMContext):
    await message.answer('Надішліть базу груп у форматі .xlsx')
    await state.set_state(ExcelFile.file_name)


@router.message(ExcelFile.file_name)
async def add_groups_excel_file(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(file_name=message.document)
    data = await state.get_data()
    document = data.get('file_name')

    if document is None:
        await message.reply("Будь ласка, надішліть правильний файл.")
        return

    if document.mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        file_info = await bot.get_file(document.file_id)
        await bot.download_file(file_info.file_path, os.getenv('EXCEL'))

        await message.reply(f'Файл отримано')

        chat_joiner = ChatJoiner(message)
        await chat_joiner.join_chats()

    else:
        await message.reply("Будь ласка, надішліть Excel файл у форматі .xlsx.")
