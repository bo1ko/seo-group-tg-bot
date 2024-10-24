from aiogram import Router, types
from aiogram.filters import CommandStart
from app.database.orm_query import orm_add_user, orm_get_user
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


#  /start
@router.message(CommandStart())
async def cmd_start(message: types.Message, session: AsyncSession):
    user = await orm_get_user(message.from_user.id, session)

    if not user:
        await orm_add_user(message.from_user.id, message.from_user.username, session)

    await message.answer('Вітаю!')
