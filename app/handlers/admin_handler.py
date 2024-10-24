import asyncio
import os

from aiogram import Router, types, F, Bot
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
from pyrogram import Client
from sqlalchemy.ext.asyncio import AsyncSession

import app.database.orm_query as rq
import app.keyboards.admin_keyboard as kb
from app.bots.authorization import TelegramLogin
from app.bots.chat_joiner import ChatJoiner
from app.bots.check_message import CheckMessage
from app.filters.check_admin import IsAdmin
from pyrogram import Client

load_dotenv()

router = Router()
router.message.filter(IsAdmin())
login_manager = TelegramLogin(os.getenv('API_ID'), os.getenv('API_HASH'))

add_chats_task = None
check_chats_task = None

auth_in_progress = False
add_chats_in_progress = False
check_chats_in_progress = False

class Auth(StatesGroup):
    waiting_for_phone_number = State()
    waiting_for_code = State()


class ExcelFile(StatesGroup):
    file_name = State()


class KeywordsState(StatesGroup):
    add_keywords = State()
    remove_keywords = State()


# admin /admin
@router.message(or_f(Command('admin'), ('Відкрити адмін меню' == F.text), ('Назад' == F.text)))
async def cmd_admin(message: types.Message, state: FSMContext):
    await message.answer('Hello, admin!', reply_markup=kb.admin_menu)
    await state.clear()


# hide admin menu
@router.message(F.text == 'Сховати адмін меню')
async def hide_admin_menu(message: types.Message):
    await message.answer('Адмін меню приховане', reply_markup=kb.hide_admin_menu)


# account
@router.message(F.text == 'Аккаунт')
async def account_manage(message: types.Message):
    if add_chats_in_progress or check_chats_in_progress:
        await message.answer('Для початку зупиніть активний процес')
    else:
        if len(os.listdir(os.getenv('SESSION_DIR'))) > 0:
            await message.answer('Виберіть дію', reply_markup=kb.account_manage)
        else:
            await message.answer('Виберіть дію', reply_markup=kb.account_add)


# add account
@router.message(F.text == 'Добавити аккаунт')
async def add_account(message: types.Message, state: FSMContext):
    global auth_in_progress

    if auth_in_progress or add_chats_in_progress or check_chats_in_progress:
        await message.answer('Для початку зупиніть активний процес')
    else:
        await message.answer('Введіть номер телефону 👇')
        await state.set_state(Auth.waiting_for_phone_number)
        auth_in_progress = True


# add account / phone
@router.message(Auth.waiting_for_phone_number)
async def phone_number_handler(message: types.Message, state: FSMContext):
    global auth_in_progress

    if message.text and message.text.isdigit():
        await state.update_data(phone_number=message.text)
        await message.answer(f"Дякую! Твій номер телефону: {message.text}. Тепер чекай код для входу.")

        asyncio.create_task(login_manager.pyrogram_login(message, state))

        await state.set_state(Auth.waiting_for_code)
    else:
        await message.answer("Введений номер телефону некоректний. Будь ласка, спробуй ще раз.")
        await state.clear()
        auth_in_progress = False


# add account / phone / code
@router.message(Auth.waiting_for_code)
async def code_handler(message: types.Message, state: FSMContext):
    global auth_in_progress

    if message.text and message.text.isdigit():
        user_data = await state.get_data()
        code_text = message.text

        await login_manager.finish_login(message, code_text, user_data)
        await state.clear()
    else:
        await message.answer("Будь ласка, введи коректний код підтвердження.")

    auth_in_progress = False


# delete account
@router.message(F.text == 'Видалити аккаунт')
async def add_account(message: types.Message, session: AsyncSession):
    if auth_in_progress or add_chats_in_progress or check_chats_in_progress:
        await message.answer('Для початку зупиніть активний процес')
    else:
        await message.answer('Аккаунт успішно видалено', reply_markup=kb.admin_menu)

        if os.path.isfile(os.getenv('SESSION_FULLNAME')):
            os.remove(os.getenv('SESSION_FULLNAME'))
            await message.answer(f"Аккаунт успішно видалений")
        else:
            await message.answer(f"Аккаунт не добавлений")
        await rq.orm_remove_channels(session)


# add groups
@router.message(F.text == 'Добавити чати')
async def add_groups(message: types.Message):
    if auth_in_progress or check_chats_in_progress:
        await message.answer('Для початку зупиніть активний процес')
    else:
        if add_chats_task and not add_chats_task.done():
            await message.answer('Для зупинення натисніть «Зупинити додавання чатів»', reply_markup=kb.stop_add_chats)
        else:
            await message.answer('Для запуску натисніть «Запустити додавання чатів»', reply_markup=kb.start_add_chats)


# add groups / start
@router.message(F.text == 'Запустити додавання чатів')
async def start_add_groups(message: types.Message, state: FSMContext):
    global add_chats_task, add_chats_in_progress

    if auth_in_progress or check_chats_in_progress:
        await message.answer('Для початку зупиніть активний процес')
    else:
        if add_chats_task and not add_chats_task.done():
            await message.answer('Додавання чатів вже працює', reply_markup=kb.admin_menu)
        else:
            await message.answer('Надішліть базу груп у форматі .xlsx')
            await state.set_state(ExcelFile.file_name)
            add_chats_in_progress = True


# add groups / get xlsx
@router.message(ExcelFile.file_name)
async def add_groups_excel_file(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession):
    global add_chats_task, add_chats_in_progress

    await state.update_data(file_name=message.document)
    data = await state.get_data()
    document = data.get('file_name')

    if document is None:
        await message.reply("Будь ласка, надішліть правильний файл.", reply_markup=kb.admin_menu)
        await state.clear()
        return

    if document.mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        file_info = await bot.get_file(document.file_id)
        await bot.download_file(file_info.file_path, os.getenv('EXCEL'))

        await message.reply(f'Файл отримано', reply_markup=kb.admin_menu)

        chat_joiner = ChatJoiner(message, session)
        add_chats_task = asyncio.create_task(chat_joiner.join_chats(session))
        await state.clear()
    else:
        await message.reply("Будь ласка, надішліть Excel файл у форматі .xlsx", reply_markup=kb.admin_menu)
        add_chats_in_progress = False


# add groups / stop
@router.message(F.text == 'Зупинити додавання чатів')
async def stop_chats_adding(message: types.Message):
    global add_chats_task, add_chats_in_progress

    if auth_in_progress or check_chats_in_progress:
        await message.answer('Для початку зупиніть активний процес')
    else:
        if add_chats_task and not add_chats_task.done():
            add_chats_task.cancel()
            await message.answer('Додавання чатів зупинено', reply_markup=kb.admin_menu)
        else:
            await message.answer('Немає активного процесу додавання чатів.', reply_markup=kb.admin_menu)
        add_chats_in_progress = False


# Chat checker
@router.message(F.text == 'Перевірка чатів')
async def check_chats(message: types.Message, session: AsyncSession):
    global check_chats_task

    if auth_in_progress or add_chats_in_progress:
        await message.answer('Для початку зупиніть активний процес')
    else:
        if check_chats_task and not check_chats_task.done():
            await message.answer('Для зупинення натисніть «Зупинити перевірку чатів»',
                                 reply_markup=kb.stop_chat_checker)
        else:
            await message.answer('Для запуску натисніть «Запустити перевірку чатів»', reply_markup=kb.start_chat_checker)

# Start chat checker
@router.message(F.text == 'Запустити перевірку чатів')
async def start_check_chats(message: types.Message, session: AsyncSession):
    global check_chats_task, check_chats_in_progress

    if auth_in_progress or add_chats_in_progress:
        await message.answer('Для початку зупиніть активний процес')
    else:
        if check_chats_task and not check_chats_task.done():
            await message.answer('Перевірка чатів вже працює', reply_markup=kb.admin_menu)
        else:
            await message.answer('Перевірка чатів запущена', reply_markup=kb.admin_menu)
            check_message = CheckMessage(message)
            check_chats_task = asyncio.create_task(check_message.check_chat(session))
        check_chats_in_progress = True

# Stop chat cheker
@router.message(F.text == 'Зупинити перевірку чатів')
async def stop_chats_adding(message: types.Message):
    global check_chats_task, check_chats_in_progress

    if auth_in_progress or add_chats_in_progress:
        await message.answer('Для початку зупиніть активний процес')
    else:
        if check_chats_task and not check_chats_task.done():
            check_chats_task.cancel()
            await message.answer('Перевірка чатів зупинена', reply_markup=kb.admin_menu)
        else:
            await message.answer('Немає активного процесу перевірки чатів.', reply_markup=kb.admin_menu)

        check_chats_in_progress = False


# Add keywords
@router.message(F.text == 'Ключові слова')
async def keywords_menu(message: types.Message):
    await message.answer('Меню "Ключові слова"', reply_markup=kb.keywords)


# Keyword list
@router.message(F.text == 'Список ключових слів')
async def keyword_list(message: types.Message, session: AsyncSession):
    orm_keywords = await rq.orm_get_keywords(session)
    keywords_str = ''

    for keyword in orm_keywords:
        keywords_str += f'{keyword.word}, '

    await message.answer(f'Список ключових слів\n\n{keywords_str}')


# Add keywords
@router.message(F.text == 'Додати ключові слова')
async def add_keywords(message: types.Message, state: FSMContext):
    await message.answer('Введіть ключові слова через кому\nПриклад: Кіт, собака, бобр')
    await state.set_state(KeywordsState.add_keywords)


@router.message(KeywordsState.add_keywords)
async def add_keywords_first_step(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(keywords=message.text)
    data = await state.get_data()
    keywords_list = data.get('keywords').replace(' ', '').split(',')
    result = await rq.orm_add_keywords(keywords_list, session)

    if result:
        await message.answer('Ключові слова успішно добавлені', reply_markup=kb.keywords)
    else:
        await message.answer('Помилка, спробуйте знову', reply_markup=kb.keywords)

    await state.clear()


# Remove keywords
@router.message(F.text == 'Видалити ключові слова')
async def remove_keywords(message: types.Message, state: FSMContext):
    await message.answer('Щоб видалити ключові слова, введіть їх через кому\nПриклад: Кіт, собака, бобр')
    await state.set_state(KeywordsState.remove_keywords)


@router.message(KeywordsState.remove_keywords)
async def remove_keywords_first_step(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(keywords=message.text)
    data = await state.get_data()
    keywords_list = data.get('keywords').replace(' ', '').split(',')
    await rq.orm_remove_keywords(keywords_list, session)

    await message.answer('Ключові слова успішно видалені', reply_markup=kb.keywords)
    await state.clear()
