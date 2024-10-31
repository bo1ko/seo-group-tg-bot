import app.keyboards.user_keyboard as kb

from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command, or_f
from app.database.orm_query import orm_add_user, orm_get_user

router = Router()


#  /start
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    user = await orm_get_user(message.from_user.id)

    if not user:
        await orm_add_user(message.from_user.id, message.from_user.username)


    subscribe_kb = kb.get_keyboard(
        'Получити доступ',
        placeholder='Щоб отримати доступ, нажміть "Отримати доступ"',
    )

    await message.answer('Привіт! Я — Бізнес Радар Європа. Моя місія — допомагати українським підприємцям швидко знаходити замовлення, роботу та клієнтів у Європі. Шукаєте нові можливості чи партнерів? Я підключу вас до великої української аудиторії в Telegram, яка також перебуває в ЄС. Я знайду найкращі пропозиції для вас. Зі мною ваш бізнес завжди на зв’язку з клієнтами!', reply_markup=subscribe_kb)

# subscribe
@router.message(or_f(Command('subscribe'), F.text.lower() =='получити доступ'))
async def cmd_subcribe(message: types.Message):
    await message.answer('hello')
