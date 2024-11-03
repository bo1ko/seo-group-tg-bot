import asyncio
import os

from datetime import datetime, timedelta

from aiogram import Router, types, F, Bot
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

import app.database.orm_query as rq
import app.keyboards.admin_keyboard as kb
import app.keyboards.user_keyboard as kb_user

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
    country = State()
    city = State()
    is_general = State()


class UserState(StatesGroup):
    add_user = State()
    remove_user = State()


# admin /admin
@router.message(
    or_f(
        Command("admin"),
        ("Відкрити адмін меню" == F.text),
        ("Назад" == F.text),
        ("◀ Назад" == F.text),
    )
)
async def cmd_admin(message: types.Message, state: FSMContext):
    await message.answer("Головне меню", reply_markup=kb.admin_menu)
    await state.clear()


# hide admin menu
@router.message(F.text == "Сховати адмін меню")
async def hide_admin_menu(message: types.Message):
    await message.answer("Адмін меню приховане", reply_markup=kb.hide_admin_menu)


# account
@router.message(F.text == "Аккаунти")
async def account_list(message: types.Message):
    accounts = await rq.orm_get_accounts()

    if not accounts:
        await message.answer("Аккаунтів немає", reply_markup=kb.account_add)
        return

    btns = {
        account.phone_number: f"account_{account.phone_number}" for account in accounts
    }

    await message.answer("Добавте новий аккаунт", reply_markup=kb.account_add)
    await message.answer(
        "або виберіть аккаунт існуючий:", reply_markup=kb.get_callback_btns(btns=btns)
    )


# callback account manage
@router.callback_query(F.data.startswith("account_"))
async def account_manage(callback: types.CallbackQuery):
    phone_number = callback.data.split("_")[-1]

    if await rq.orm_is_account_active(phone_number):
        await callback.message.edit_text(
            "Аккаунт зараз активний. Для початку зупиніть активний процес."
        )
        return

    btns = {"Видалити": f"remove_{phone_number}", "Назад": "back_to_accounts"}

    await callback.message.edit_text(
        "Редагування аккаунту", reply_markup=kb.get_callback_btns(btns=btns)
    )


# callback account delete
@router.callback_query(F.data.startswith("remove_"))
async def account_remove(callback: types.CallbackQuery):
    phone_number = callback.data.split("_")[-1]
    is_active = await rq.orm_is_account_active(phone_number)
    btns = {"Назад": "back_to_accounts"}

    if is_active:
        await callback.message.edit_text(
            "Аккаунт зараз активний. Для початку зупиніть активний процес.",
            reply_markup=kb.get_callback_btns(btns=btns),
        )
        return

    file_path = os.path.join("s", f"{phone_number}.")

    if os.path.exists(file_path):
        os.remove(file_path)

    await rq.orm_remove_account(phone_number)
    await callback.message.edit_text("Обліковий запис та файл сесії видалено.")


# callback back
@router.callback_query(F.data == "back_to_accounts")
async def account_back(callback: types.CallbackQuery, state: FSMContext):
    accounts = await rq.orm_get_accounts()

    if not accounts:
        await callback.answer()
        await callback.message.answer("Аккаунтів немає", reply_markup=kb.account_add)
        return

    btns = {
        account.phone_number: f"account_{account.phone_number}" for account in accounts
    }

    await callback.message.edit_text(
        "Виберіть аккаунт:", reply_markup=kb.get_callback_btns(btns=btns)
    )
    await state.clear()


# add account
@router.message(F.text == "Добавити аккаунт")
async def add_account(message: types.Message, state: FSMContext):
    await message.answer(
        "Введіть API ID 👇\n(получити його можна тут: https://my.telegram.org/auth)"
    )
    await state.set_state(Auth.waiting_for_api_id)


# add account / api_id
@router.message(Auth.waiting_for_api_id)
async def get_api_id(message: types.Message, state: FSMContext):
    await state.update_data(api_id=message.text)
    await message.answer("Введіть API HASH 👇")
    await state.set_state(Auth.waiting_for_api_hash)


# add account / api_hash
@router.message(Auth.waiting_for_api_hash)
async def get_api_hash(message: types.Message, state: FSMContext):
    await state.update_data(api_hash=message.text)
    await message.answer("Введіть номер телефону 👇")
    await state.set_state(Auth.waiting_for_phone_number)


# add account / phone
@router.message(Auth.waiting_for_phone_number)
async def phone_number_handler(message: types.Message, state: FSMContext):
    if message.text and message.text.isdigit():
        await state.update_data(phone_number=message.text)
        await message.answer(
            f"Дякую! Твій номер телефону: {message.text}. Тепер чекай код для входу."
        )
        data = await state.get_data()
        phone_number = data.get("phone_number")
        api_id = data.get("api_id")
        api_hash = data.get("api_hash")

        if api_id and api_hash and phone_number:
            await rq.orm_add_account(phone_number, api_id, api_hash)

            global login_manager

            login_manager = TelegramLogin()
            asyncio.create_task(login_manager.pyrogram_login(message, state))

            await state.set_state(Auth.waiting_for_code)
        else:
            await message.answer(
                "Ви ввели щось не правильно! Спробуйте знову.",
                reply_markup=kb.admin_menu,
            )
    else:
        await message.answer(
            "Введений номер телефону некоректний. Будь ласка, спробуй ще раз."
        )
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
@router.message(F.text == "Добавити чати")
async def add_groups(message: types.Message, state: FSMContext):
    accounts = await rq.orm_get_accounts()

    if not accounts:
        await message.answer("Аккаунтів немає", reply_markup=kb.admin_menu)
        return

    await message.answer("Меню «Добавити чати»", reply_markup=kb.back)
    print(add_chats_task)

    if add_chats_task and not add_chats_task.done():
        btns = {"Зупинити додавання чатів": "stop_group_adding"}
        await message.answer(
            "Додавання чатів вже працює", reply_markup=kb.get_callback_btns(btns=btns)
        )
        return
    else:
        await message.answer(
            "Надішліть базу груп у форматі .xlsx", reply_markup=kb.back
        )
        await state.set_state(ExcelFile.file_name)


# add groups / stop
@router.callback_query(F.data == "stop_group_adding")
async def stop_group_adding(callback: types.CallbackQuery):
    global add_chats_task

    if add_chats_task and not add_chats_task.done():
        add_chats_task.cancel()
        await callback.answer()
        await callback.message.edit_text("Починаю зупиняти процес...", kb.admin_menu)
    else:
        await callback.message.answer(
            "Немає активного процесу додавання чатів.", reply_markup=kb.admin_menu
        )


# add groups / get xlsx
@router.message(ExcelFile.file_name)
async def add_groups_excel_file(message: types.Message, state: FSMContext, bot: Bot):
    global add_chats_task

    await state.update_data(file_name=message.document)
    data = await state.get_data()
    document = data.get("file_name")

    if document is None:
        await message.reply(
            "Будь ласка, надішліть правильний файл.", reply_markup=kb.admin_menu
        )
        await state.clear()
        return

    # If document is lxml create async task for ChatJoiner
    if (
        document.mime_type
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ):
        file_info = await bot.get_file(document.file_id)
        await bot.download_file(file_info.file_path, os.getenv("EXCEL"))

        await message.reply(f"Файл отримано")
        await message.answer("Введіть країну", reply_markup=kb.back)
        await state.set_state(ExcelFile.country)
    else:
        await message.reply(
            "Будь ласка, надішліть Excel файл у форматі .xlsx",
            reply_markup=kb.admin_menu,
        )
        await state.clear()


@router.message(ExcelFile.country)
async def add_groups_excel_file_first(message: types.Message, state: FSMContext):
    await state.update_data(country=message.text)
    await message.answer("Введіть місто", reply_markup=kb.back)
    await state.set_state(ExcelFile.city)


@router.message(ExcelFile.city)
async def add_groups_excel_file_second(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Тип загальний?\nВідповідь: Так / Ні", reply_markup=kb.back)
    await state.set_state(ExcelFile.is_general)


@router.message(ExcelFile.is_general)
async def add_groups_excel_file_third(message: types.Message, state: FSMContext):
    global add_chats_task

    await state.update_data(is_general=message.text)
    data = await state.get_data()

    country = data.get("country")
    if country:
        country = country.lower()
    
    city = data.get("city")
    if city:
        city = city.lower()
    
    is_general = data.get("is_general")

    if is_general.lower() == "так":
        is_general = True
    elif is_general.lower() == "ні":
        is_general = False
    else:
        await message.answer(
            "Ви ввели невірну відповідь. Процес завершено неуспішно.",
            reply_markup=kb.admin_menu,
        )
        await state.clear()
        return

    await message.answer("Дані збережено, запускаю процес!", reply_markup=kb.admin_menu)
    await state.clear()

    chat_joiner = ChatJoiner(message)
    # await chat_joiner.join_chats(country, city, is_general)
    add_chats_task = asyncio.create_task(chat_joiner.join_chats(country, city, is_general))


# Chat checker
@router.message(F.text == "Перевірка чатів")
async def check_chats(message: types.Message):
    global check_chats_task

    if check_chats_task and not check_chats_task.done():
        await message.answer(
            "Для зупинення натисніть «Зупинити перевірку чатів»",
            reply_markup=kb.stop_chat_checker,
        )
    else:
        await message.answer(
            "Для запуску натисніть «Запустити перевірку чатів»",
            reply_markup=kb.start_chat_checker,
        )


# Start chat checker
@router.message(F.text == "Запустити перевірку чатів")
async def start_check_chats(message: types.Message):
    global check_chats_task

    accounts = await rq.orm_get_accounts()

    if not accounts:
        await message.answer("Аккаунтів немає", reply_markup=kb.account_add)
        return

    if check_chats_task and not check_chats_task.done():
        await message.answer("Перевірка чатів вже працює", reply_markup=kb.admin_menu)
    else:
        await message.answer("Перевірка чатів запущена", reply_markup=kb.admin_menu)
        check_message = CheckMessage(message)
        check_chats_task = asyncio.create_task(check_message.check_chat())


# Stop chat cheker
@router.message(F.text == "Зупинити перевірку чатів")
async def stop_chats_adding(message: types.Message):
    global check_chats_task

    if check_chats_task and not check_chats_task.done():
        check_chats_task.cancel()
        await message.answer("Перевірка чатів зупинена", reply_markup=kb.admin_menu)
    else:
        await message.answer(
            "Немає активного процесу перевірки чатів.", reply_markup=kb.admin_menu
        )


# Users
@router.message(F.text == "Користувачі")
async def users_manage(message: types.Message):
    await message.answer("Керування користувачами", reply_markup=kb.users_manage)


# Users list
@router.message(F.text == "Список користувачів")
async def users_manage(message: types.Message):
    users = await rq.orm_get_users()
    users_str = "Список користувачів\n\n"

    for user in users:
        users_str += f"{user.name}\n\n"

    await message.answer(users_str, reply_markup=kb.users_manage)


# Add user
@router.message(F.text == "Добавити користувача")
async def add_user(message: types.Message, state: FSMContext):
    await message.answer("Введіть юзернейм користувача\n\n❌ - @bobr\n✔ - bobr")
    await state.set_state(UserState.add_user)


@router.message(UserState.add_user)
async def add_user_first(message: types.Message, state: FSMContext):
    await state.update_data(user=message.text)
    data = await state.get_data()
    username = data.get("user")

    result = await rq.orm_add_user_by_name(username)

    if result:
        await message.answer(
            "Користувач добавлений успішно", reply_markup=kb.users_manage
        )
    else:
        await message.answer("Користувача не вдалося додати. Спробуйте знову!")

    await state.clear()


@router.message(F.text == "Видалити користувача")
async def remove_user(message: types.Message, state: FSMContext):
    await message.answer("Введіть юзернейм користувача\n\n❌ - @bobr\n✔ - bobr")
    await state.set_state(UserState.remove_user)


@router.message(UserState.remove_user)
async def remove_user_first(message: types.Message, state: FSMContext):
    await state.update_data(user=message.text)
    data = await state.get_data()
    username = data.get("user")

    result = await rq.orm_remove_user(username)

    if result:
        await message.answer(
            "Користувач видалений успішно", reply_markup=kb.users_manage
        )
    else:
        await message.answer("Користувача не вдалося видалити. Спробуйте знову!")


########## Subscribe ##########


class Subscriber(StatesGroup):
    add_tg_id = State()
    remove_tg_id = State()


KEY_WORDS = {
    "список підписників": "Список підписників 📃",
    "історія підписок": "Історія підписок 📖",
    "видати підписку": "Видати підписку ✅",
    "видалити підписку": "Видалити підписку ❌",
    "назад": "◀ Назад",
}

SUBSCRIBE_KB = kb.get_keyboard(
    KEY_WORDS["список підписників"],
    KEY_WORDS["історія підписок"],
    KEY_WORDS["видати підписку"],
    KEY_WORDS["видалити підписку"],
    KEY_WORDS["назад"],
    placeholder="Виберіть пункт меню...",
    sizes=(2,),
)

PERIOD_KB = kb.get_callback_btns(
    btns={
        "3 дня": "subscription_period_3",
        "30 днів": "subscription_period_30",
        "60 днів": "subscription_period_60",
        "90 днів": "subscription_period_90",
    }
)


@router.message(
    or_f(Command("user_subscribe"), "налаштування підписок" == F.text.lower())
)
async def cmd_user_subscribe(message: types.Message):
    await message.answer(
        'Ви перейшли в меню "Налаштування підписок"', reply_markup=SUBSCRIBE_KB
    )


@router.message(F.text == KEY_WORDS["список підписників"])
async def subscribe_list(message: types.Message):
    orm_data = await rq.orm_get_subscribers()

    if orm_data:
        await message.answer("Список підписників 👇")

        for item in orm_data:
            if item.is_subscribed:
                start_date = item.start_subscription_date.strftime("%Y-%m-%d")
                end_date = item.end_subscription_date.strftime("%Y-%m-%d")

                await message.answer(
                    f"<code>{item.user_id}</code> | Активна від {start_date} до {end_date}"
                )
    else:
        await message.answer("Немає підписників")


@router.message(F.text == KEY_WORDS["історія підписок"])
async def subscribe_history(message: types.Message):
    orm_data = await rq.orm_get_subscribers()

    if orm_data:
        await message.answer("Історія підписок 👇")

        for item in orm_data:
            start_date = item.start_subscription_date.strftime("%Y-%m-%d")
            end_date = item.end_subscription_date.strftime("%Y-%m-%d")

            if item.is_subscribed:
                await message.answer(
                    f"<code>{item.user_id}</code> | {'Активна ✅'} | Активна від {start_date} до {end_date}"
                )
            else:
                await message.answer(
                    f"<code>{item.user_id}</code> | {'Неактивна ❌'} | Була активна від {start_date} до {end_date}"
                )
    else:
        await message.answer("Немає підписок")


@router.message(F.text == KEY_WORDS["видати підписку"])
async def add_subscriber(message: types.Message, state: FSMContext):
    await message.answer("Введіть ID підписника: ", reply_markup=kb.back)
    await state.set_state(Subscriber.add_tg_id)


@router.message(Subscriber.add_tg_id)
async def add_subscriber_first(message: types.Message, state: FSMContext):
    await state.update_data(tg_id=message.text)
    data = await state.get_data()

    try:
        tg_id = int(data.get("tg_id"))

        if tg_id:
            await message.answer("На скільки видати підписку?", reply_markup=PERIOD_KB)
    except ValueError:
        await message.answer("Ви ввели некоректний ID", reply_markup=PERIOD_KB)
        await state.clear()


@router.callback_query(F.data.startswith("subscription_period_"))
async def subscription_period(
    callback: types.CallbackQuery, state: FSMContext, bot: Bot
):
    period = int(callback.data.split("_")[-1])
    data = await state.get_data()
    tg_id = data.get("tg_id")

    await callback.answer()

    user_data = await rq.orm_get_user(tg_id)

    if not user_data:
        await callback.message.answer(
            "❌ Користувача з таким айді не знайдено в базі ❌\n\nДля початку користувач має запустити бота через кнопку START, щоб почати індексуватися в базі.",
            reply_markup=SUBSCRIBE_KB,
        )
        return

    subscriber_result = await rq.orm_get_subscriber(tg_id)
    start_date = datetime.now()
    end_date = start_date + timedelta(days=period)

    if not subscriber_result:
        result = await rq.orm_add_subscriber(tg_id, start_date, end_date)
    else:
        await rq.orm_disable_all_subscriptions(tg_id)
        result = await rq.orm_add_subscriber(tg_id, start_date, end_date)

    if result:
        if user_data.name:
            await callback.message.answer(
                f"Підписка видана на {period} днів для користувача @{user_data.name} ({tg_id})",
                reply_markup=SUBSCRIBE_KB,
            )
        else:
            await callback.message.answer(
                f"Підписка видана на {period} днів для користувача {tg_id}",
                reply_markup=SUBSCRIBE_KB,
            )

        await bot.send_message(
            chat_id=tg_id,
            text=f'Вам була видана підписка на {period} {"дня" if period == 3 else "днів"}',
            reply_markup=kb_user.user_menu,
        )
    else:
        await callback.message.answer(f"{result}")

    await state.clear()


@router.message(F.text == KEY_WORDS["видалити підписку"])
async def remove_subscriber(message: types.Message, state: FSMContext):
    await message.answer(
        "Введіть ID користувача, якому хочете видалити підписку", reply_markup=kb.back
    )
    await state.set_state(Subscriber.remove_tg_id)


@router.message(Subscriber.remove_tg_id)
async def remove_subscriber_first(message: types.Message, state: FSMContext):
    await state.update_data(tg_id=message.text)
    data = await state.get_data()

    try:
        tg_id = data.get("tg_id")

        user_data = await rq.orm_get_user(tg_id)

        if user_data:
            result = await rq.orm_disable_active_subscribers(tg_id)

            if result:
                await message.answer(
                    f"Підписка у користувача {f'@{user_data.name} ' if user_data.name else ' '}(<code>{tg_id}</code>) успішно видалена.",
                    reply_markup=SUBSCRIBE_KB,
                )
            else:
                await message.answer(f"Щось пішло не так 😢", reply_markup=SUBSCRIBE_KB)
        else:
            await message.answer("Ви ввели некоректний ID", reply_markup=SUBSCRIBE_KB)
    except:
        await message.answer("Ви ввели некоректний ID", reply_markup=SUBSCRIBE_KB)

    await state.clear()
