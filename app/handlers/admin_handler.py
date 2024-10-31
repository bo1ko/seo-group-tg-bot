import asyncio
import os

from aiogram import Router, types, F, Bot
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

import app.database.orm_query as rq
import app.keyboards.admin_keyboard as kb
from app.bots.authorization import TelegramLogin
from app.bots.chat_joiner import ChatJoiner
from app.bots.check_message import CheckMessage
from app.filters.check_admin import IsAdmin

load_dotenv()

router = Router()
router.message.filter(IsAdmin())

add_chats_task = None
check_chats_task = None

login_manager = None

auth_in_progress = False
add_chats_in_progress = False
check_chats_in_progress = False


class Auth(StatesGroup):
    waiting_for_api_id = State()
    waiting_for_api_hash = State()
    waiting_for_phone_number = State()
    waiting_for_code = State()


class ExcelFile(StatesGroup):
    file_name = State()


class KeywordsState(StatesGroup):
    add_keywords = State()
    remove_keywords = State()


class UserState(StatesGroup):
    add_user = State()
    remove_user = State()


# admin /admin
@router.message(or_f(Command('admin'), ('Відкрити адмін меню' == F.text), ('Назад' == F.text)))
async def cmd_admin(message: types.Message, state: FSMContext):
    await message.answer('Hello, admin!', reply_markup=kb.admin_menu)
    await state.clear()


# hide admin menu
@router.message(F.text == 'Сховати адмін меню')
async def hide_admin_menu(message: types.Message):
    await message.answer('Адмін меню приховане', reply_markup=kb.hide_admin_menu)
    print(auth_in_progress, add_chats_in_progress, check_chats_in_progress)


# account
@router.message(F.text == 'Аккаунт')
async def account_list(message: types.Message):
    accounts = await rq.orm_get_accounts()

    if not accounts:
        await message.answer('Аккаунтів немає', reply_markup=kb.account_add)
        return

    btns = {account.phone_number: f'account_{account.phone_number}' for account in accounts}

    await message.answer('Добавте новий аккаунт', reply_markup=kb.account_add)
    await message.answer("або виберіть аккаунт існуючий:", reply_markup=kb.get_callback_btns(btns=btns))


# callback account manage
@router.callback_query(F.data.startswith('account_'))
async def account_manage(callback: types.CallbackQuery):
    phone_number = callback.data.split('_')[-1]

    if await rq.orm_is_account_active(phone_number):
        await callback.message.edit_text('Аккаунт зараз активний. Для початку зупиніть активний процес.')
        return

    btns = {
        'Видалити': f'remove_{phone_number}',
        'Назад': 'back_to_accounts'
    }

    await callback.message.edit_text('Редагування аккаунту', reply_markup=kb.get_callback_btns(btns=btns))


# callback account delete
@router.callback_query(F.data.startswith('remove_'))
async def account_remove(callback: types.CallbackQuery):
    phone_number = callback.data.split('_')[-1]
    is_active = await rq.orm_is_account_active(phone_number)
    btns = {'Назад': 'back_to_accounts'}

    if is_active:
        await callback.message.edit_text('Аккаунт зараз активний. Для початку зупиніть активний процес.',
                                         reply_markup=kb.get_callback_btns(btns=btns))
        return

    file_path = os.path.join('s', f'{phone_number}.')

    if os.path.exists(file_path):
        os.remove(file_path)

    await rq.orm_remove_account(phone_number)
    await callback.message.edit_text("Обліковий запис та файл сесії видалено.")


# callback back
@router.callback_query(F.data == 'back_to_accounts')
async def account_back(callback: types.CallbackQuery, state: FSMContext):
    accounts = await rq.orm_get_accounts()

    if not accounts:
        await callback.answer()
        await callback.message.answer('Аккаунтів немає', reply_markup=kb.account_add)
        return

    btns = {account.phone_number: f'account_{account.phone_number}' for account in accounts}

    await callback.message.edit_text("Виберіть аккаунт:", reply_markup=kb.get_callback_btns(btns=btns))
    await state.clear()


# add account
@router.message(F.text == 'Добавити аккаунт')
async def add_account(message: types.Message, state: FSMContext):
    accounts = await rq.orm_get_accounts()

    for account in accounts:
        active_type = await rq.orm_check_active_type(account.phone_number)

        if account.is_active and active_type != 'check':
            await message.answer('У вас є активні аккаунти. Для початку зупиніть активний процес.')
            return

    await message.answer('Введіть API ID 👇\n(получити його можна тут: https://my.telegram.org/auth)')
    await state.set_state(Auth.waiting_for_api_id)


# add account / api_id
@router.message(Auth.waiting_for_api_id)
async def get_api_id(message: types.Message, state: FSMContext):
    await state.update_data(api_id=message.text)
    await message.answer('Введіть API HASH 👇')
    await state.set_state(Auth.waiting_for_api_hash)


# add account / api_hash
@router.message(Auth.waiting_for_api_hash)
async def get_api_hash(message: types.Message, state: FSMContext):
    await state.update_data(api_hash=message.text)
    await message.answer('Введіть номер телефону 👇')
    await state.set_state(Auth.waiting_for_phone_number)


# add account / phone
@router.message(Auth.waiting_for_phone_number)
async def phone_number_handler(message: types.Message, state: FSMContext):
    if message.text and message.text.isdigit():
        await state.update_data(phone_number=message.text)
        await message.answer(f"Дякую! Твій номер телефону: {message.text}. Тепер чекай код для входу.")
        data = await state.get_data()
        phone_number = data.get('phone_number')
        api_id = data.get('api_id')
        api_hash = data.get('api_hash')

        if api_id and api_hash and phone_number:
            await rq.orm_add_account(phone_number, api_id, api_hash)

            global login_manager

            login_manager = TelegramLogin()
            asyncio.create_task(login_manager.pyrogram_login(message, state))

            await state.set_state(Auth.waiting_for_code)
        else:
            await message.answer('Ви ввели щось не правильно! Спробуйте знову.', reply_markup=kb.admin_menu)
    else:
        await message.answer("Введений номер телефону некоректний. Будь ласка, спробуй ще раз.")
        await state.clear()


# add account / phone / code
@router.message(Auth.waiting_for_code)
async def code_handler(message: types.Message, state: FSMContext):
    global auth_in_progress

    if message.text and message.text.isdigit():
        code_text = message.text

        await login_manager.finish_login(message, code_text)
        await state.clear()
    else:
        await message.answer("Будь ласка, введи коректний код підтвердження.")

    auth_in_progress = False


# add groups
@router.message(F.text == 'Добавити чати')
async def add_groups(message: types.Message):
    accounts = await rq.orm_get_accounts()

    if not accounts:
        await message.answer('Аккаунтів немає', reply_markup=kb.admin_menu)
        return

    btns = {account.phone_number: f'add_chats_{account.phone_number}' for account in accounts}

    await message.answer('Меню «Добавити чати»', reply_markup=kb.back)
    await message.answer("Виберіть аккаунт:", reply_markup=kb.get_callback_btns(btns=btns))


# Callback / Groups / Choose number
@router.callback_query(F.data.startswith('add_chats_'))
async def groups_choose_number(callback: types.CallbackQuery, state: FSMContext):
    phone_number = callback.data.split('_')[-1]
    is_active = await rq.orm_is_account_active(phone_number)
    active_type = await rq.orm_check_active_type(phone_number)

    if is_active and active_type != 'group':
        await callback.message.edit_text('Вже є активний процес додавання в чати!')
        return

    await state.update_data(phone_number=phone_number)
    await callback.message.edit_text('Запускаю додавання чатів...')
    await start_add_groups(callback, state)


# add groups / start
@router.callback_query(F.date == 'start_add_groups')
async def start_add_groups(callback: types.CallbackQuery, state: FSMContext):
    global add_chats_task

    if add_chats_task and not add_chats_task.done():
        btns = {'Зупинити додавання чатів': 'stop_group_adding'}
        await callback.message.edit_text('Додавання чатів вже працює', reply_markup=kb.get_callback_btns(btns=btns))
        return
    else:
        await callback.message.answer('Надішліть базу груп у форматі .xlsx', reply_markup=kb.back)
        await state.set_state(ExcelFile.file_name)


# add groups / stop
@router.callback_query(F.data == 'stop_group_adding')
async def stop_group_adding(callback: types.CallbackQuery):
    global add_chats_task

    if add_chats_task and not add_chats_task.done():
        add_chats_task.cancel()
        await callback.answer()
        await callback.message.edit_text('Починаю зупиняти процес...')
        await callback.message.answer('Додавання чатів зупинено', reply_markup=kb.admin_menu)
    else:
        await callback.message.answer('Немає активного процесу додавання чатів.', reply_markup=kb.admin_menu)


# add groups / get xlsx
@router.message(ExcelFile.file_name)
async def add_groups_excel_file(message: types.Message, state: FSMContext, bot: Bot):
    global add_chats_task

    await state.update_data(file_name=message.document)
    data = await state.get_data()
    document = data.get('file_name')
    phone_number = data.get('phone_number')

    if document is None:
        await message.reply("Будь ласка, надішліть правильний файл.", reply_markup=kb.admin_menu)
        await state.clear()
        return

    # If document is lxml create async task for ChatJoiner
    if document.mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        file_info = await bot.get_file(document.file_id)
        await bot.download_file(file_info.file_path, os.getenv('EXCEL'))

        await message.reply(f'Файл отримано, запускаю процес!')

        chat_joiner = ChatJoiner(phone_number, message)
        add_chats_task = asyncio.create_task(chat_joiner.join_chats())
    else:
        await message.reply("Будь ласка, надішліть Excel файл у форматі .xlsx", reply_markup=kb.admin_menu)

    await state.clear()


# Chat checker
@router.message(F.text == 'Перевірка чатів')
async def check_chats(message: types.Message):
    global check_chats_task

    if check_chats_task and not check_chats_task.done():
        await message.answer('Для зупинення натисніть «Зупинити перевірку чатів»',
                             reply_markup=kb.stop_chat_checker)
    else:
        await message.answer('Для запуску натисніть «Запустити перевірку чатів»',
                             reply_markup=kb.start_chat_checker)


# Start chat checker
@router.message(F.text == 'Запустити перевірку чатів')
async def start_check_chats(message: types.Message):
    global check_chats_task

    accounts = await rq.orm_get_accounts()

    if not accounts:
        await message.answer('Аккаунтів немає', reply_markup=kb.account_add)
        return

    if (check_chats_task and not check_chats_task.done()):
        await message.answer('Перевірка чатів вже працює', reply_markup=kb.admin_menu)
    else:
        accounts = await rq.orm_get_accounts()

        for account in accounts:
            active_type = await rq.orm_check_active_type(account.phone_number)

            if account.is_active and active_type != 'check':
                await message.answer('У вас є активні аккаунти. Для початку зупиніть активний процес.')
                return

        await message.answer('Перевірка чатів запущена', reply_markup=kb.admin_menu)
        check_message = CheckMessage(message)
        check_chats_task = asyncio.create_task(check_message.check_chat())


# Stop chat cheker
@router.message(F.text == 'Зупинити перевірку чатів')
async def stop_chats_adding(message: types.Message):
    global check_chats_task

    if check_chats_task and not check_chats_task.done():
        check_chats_task.cancel()
        await message.answer('Перевірка чатів зупинена', reply_markup=kb.admin_menu)
    else:
        await message.answer('Немає активного процесу перевірки чатів.', reply_markup=kb.admin_menu)


# Add keywords
@router.message(F.text == 'Ключові слова')
async def keywords_menu(message: types.Message):
    await message.answer('Меню "Ключові слова"', reply_markup=kb.keywords)


# Keyword list
@router.message(F.text == 'Список ключових слів')
async def keyword_list(message: types.Message):
    # orm_keywords = await rq.orm_get_keywords()
    keywords_str = ''

    # for keyword in orm_keywords:
        # keywords_str += f'{keyword.word}, '

    await message.answer(f'Список ключових слів\n\n{keywords_str}')


# Add keywords
@router.message(F.text == 'Додати ключові слова')
async def add_keywords(message: types.Message, state: FSMContext):
    await message.answer('Введіть ключові слова через кому\nПриклад: Кіт, собака, бобр')
    await state.set_state(KeywordsState.add_keywords)


@router.message(KeywordsState.add_keywords)
async def add_keywords_first_step(message: types.Message, state: FSMContext):
    await state.update_data(keywords=message.text)
    data = await state.get_data()
    keywords_list = [i.strip() for i in data.get('keywords').split(',')]
    result = await rq.orm_add_keywords(keywords_list)

    if result:
        await message.answer('Ключові слова успішно добавлені', reply_markup=kb.keywords)
    else:
        await message.answer('Таке ключове слово вже є в базі', reply_markup=kb.keywords)

    await state.clear()


# Remove keywords
@router.message(F.text == 'Видалити ключові слова')
async def remove_keywords(message: types.Message, state: FSMContext):
    await message.answer('Щоб видалити ключові слова, введіть їх через кому\nПриклад: Кіт, собака, бобр')
    await state.set_state(KeywordsState.remove_keywords)


@router.message(KeywordsState.remove_keywords)
async def remove_keywords_first_step(message: types.Message, state: FSMContext):
    await state.update_data(keywords=message.text)
    data = await state.get_data()
    keywords_list = data.get('keywords').replace(' ', '').split(',')
    await rq.orm_remove_keywords(keywords_list)

    await message.answer('Ключові слова успішно видалені', reply_markup=kb.keywords)
    await state.clear()


# Users
@router.message(F.text == 'Користувачі')
async def users_manage(message: types.Message):
    await message.answer('Керування користувачами', reply_markup=kb.users_manage)


# Users list
@router.message(F.text == 'Список користувачів')
async def users_manage(message: types.Message):
    users = await rq.orm_get_users()
    users_str = 'Список користувачів\n\n'

    for user in users:
        users_str += f'{user.name}\n\n'

    await message.answer(users_str, reply_markup=kb.users_manage)


# Add user
@router.message(F.text == 'Добавити користувача')
async def add_user(message: types.Message, state: FSMContext):
    await message.answer('Введіть юзернейм користувача\n\n❌ - @bobr\n✔ - bobr')
    await state.set_state(UserState.add_user)


@router.message(UserState.add_user)
async def add_user_first(message: types.Message, state: FSMContext):
    await state.update_data(user=message.text)
    data = await state.get_data()
    username = data.get('user')

    result = await rq.orm_add_user_by_name(username)

    if result:
        await message.answer('Користувач добавлений успішно', reply_markup=kb.users_manage)
    else:
        await message.answer('Користувача не вдалося додати. Спробуйте знову!')

    await state.clear()


@router.message(F.text == 'Видалити користувача')
async def remove_user(message: types.Message, state: FSMContext):
    await message.answer('Введіть юзернейм користувача\n\n❌ - @bobr\n✔ - bobr')
    await state.set_state(UserState.remove_user)


@router.message(UserState.remove_user)
async def remove_user_first(message: types.Message, state: FSMContext):
    await state.update_data(user=message.text)
    data = await state.get_data()
    username = data.get('user')

    result = await rq.orm_remove_user(username)

    if result:
        await message.answer('Користувач видалений успішно', reply_markup=kb.users_manage)
    else:
        await message.answer('Користувача не вдалося видалити. Спробуйте знову!')


########## Subscribe ##########
@router.message(or_f(Command('user_subscribe'), F.text.lower('Налаштування підписок')))
async def cmd_user_subscribe(message: types.Message):
    ...
