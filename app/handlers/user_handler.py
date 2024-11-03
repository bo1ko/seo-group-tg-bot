import os

import app.keyboards.user_keyboard as kb

from aiogram import Router, types, F, Bot
from aiogram.filters import CommandStart, Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

import app.database.orm_query as rq

from app.filters.check_sub_user import IsSubUser
from app.filters.check_chat_type import ChatTypeFilter


load_dotenv()

router = Router()

public_router = Router()
public_router.message.filter(ChatTypeFilter(['private']))

private_router = Router()
private_router.message.filter(IsSubUser(), ChatTypeFilter(['private']))

KEY_WORDS = {
    'получити доступ': '🔑 Получити доступ 🔑',
}

class Feedback(StatesGroup):
    question = State()

#  /start
@public_router.message(CommandStart())
async def cmd_start(message: types.Message):
    if await IsSubUser().__call__(message):
        await message.answer('Ви перейшли в головне меню', reply_markup=kb.user_menu)
        return

    user = await rq.orm_get_user(str(message.from_user.id))

    if not user:
        await rq.orm_add_user(str(message.from_user.id), message.from_user.username)

    subscribe_kb = kb.get_keyboard(
        KEY_WORDS['получити доступ'],
        placeholder='Щоб отримати доступ, нажміть "Отримати доступ"',
    )

    await message.answer(
        'Привіт! Я — Бізнес Радар Європа. Моя місія — допомагати українським підприємцям швидко знаходити замовлення, роботу та клієнтів у Європі. Шукаєте нові можливості чи партнерів? Я підключу вас до великої української аудиторії в Telegram, яка також перебуває в ЄС. Я знайду найкращі пропозиції для вас. Зі мною ваш бізнес завжди на зв’язку з клієнтами!',
        reply_markup=subscribe_kb)


# subscribe
@public_router.message(or_f(Command('subscribe'), KEY_WORDS['получити доступ'] == F.text))
async def cmd_subcribe(message: types.Message):
    await message.answer(
        f'Твій телеграм ID: <code>{message.from_user.id}</code>\n\nЩоб отримати доступ, напиши сюди\n 👉 @magisteroffski')


### MAIN MENU
@private_router.message(F.text == 'Головне меню')
async def main_menu(message: types.Message, state: FSMContext):
    await message.answer('Ви перейшли в "Головне меню"', reply_markup=kb.user_menu)
    await state.clear()

### KEYWORDS
class KeywordsState(StatesGroup):
    add_keywords = State()
    remove_keywords = State()


# Add keywords
@private_router.message(F.text == "Ключові слова")
async def keywords_menu(message: types.Message):
    await message.answer('Меню "Ключові слова"', reply_markup=kb.keywords)


# Keyword list
@private_router.message(F.text == "Список ключових слів")
async def keyword_list(message: types.Message):
    orm_keywords = await rq.orm_get_keywords(str(message.from_user.id))

    if orm_keywords:
        keywords_str = ', '.join(orm_keywords)
        await message.answer(f"Список ключових слів\n\n{keywords_str}")
    else:
        await message.answer('Немає ключових слів')


# Add keywords
@private_router.message(F.text == "Додати ключові слова")
async def add_keywords(message: types.Message, state: FSMContext):
    await message.answer("Введіть ключові слова через кому\nПриклад: Кіт, собака, бобр", reply_markup=kb.main)
    await state.set_state(KeywordsState.add_keywords)


@private_router.message(KeywordsState.add_keywords)
async def add_keywords_first_step(message: types.Message, state: FSMContext):
    await state.update_data(keywords=message.text)
    data = await state.get_data()
    keywords_list = [i.strip() for i in data.get("keywords").split(",")]
    result = await rq.orm_add_keywords(str(message.from_user.id), keywords_list)

    if result:
        await message.answer(
            "Ключові слова успішно добавлені", reply_markup=kb.keywords
        )
    else:
        await message.answer(
            "Таке ключове слово вже є в базі", reply_markup=kb.keywords
        )

    await state.clear()


# Remove keywords
@private_router.message(F.text == "Видалити ключові слова")
async def remove_keywords(message: types.Message, state: FSMContext):
    await message.answer(
        "Щоб видалити ключові слова, введіть їх через кому\nПриклад: Кіт, собака, бобр",
        reply_markup=kb.main
    )
    await state.set_state(KeywordsState.remove_keywords)


@private_router.message(KeywordsState.remove_keywords)
async def remove_keywords_first_step(message: types.Message, state: FSMContext):
    await state.update_data(keywords=message.text)
    data = await state.get_data()
    keywords_list = [i.strip() for i in data.get("keywords").split(",")]
    result = await rq.orm_remove_keywords(str(message.from_user.id), keywords_list)

    if result:
        await message.answer("Ключові слова успішно видалені", reply_markup=kb.keywords)
    else:
        await message.answer("Щось пішло не так 😢, спробуйте знову.", reply_markup=kb.keywords)
    await state.clear()

### Feedback
@private_router.message(F.text == "Зв'язок з адміністратором")
async def feedback(message: types.Message, state: FSMContext):
    await message.answer('Напишіть сюди своє запитання 👇', reply_markup=kb.main)
    await state.set_state(Feedback.question)

@private_router.message(Feedback.question)
async def feedback_first(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(question=message.text)
    data = await state.get_data()
    question = data.get("question")

    if question:
        await message.answer(f'<blockquote>{question}</blockquote>\n\nВаше повідомлення успішно надіслано адміністратору.', reply_markup=kb.user_menu)
        await bot.send_message(
            chat_id=os.getenv('CHAT_ID'),
            text=f'Повідомлення від користувача {f"@{message.from_user.username}" if message.from_user.username else "-"} (<code>{message.from_user.id}</code>)\n\n<blockquote>{question}</blockquote>\n\n<code>/answer {message.from_user.id} </code>',
        )
    else:
        await message.answer('Щось пішло не так 😢, спробуйте знову.', reply_markup=kb.user_menu)

    await state.clear()
router.include_router(public_router)
router.include_router(private_router)
