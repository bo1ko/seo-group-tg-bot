from aiogram.filters import Filter
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.orm_query import orm_is_admin


class IsAdmin(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message, session: AsyncSession):
        return await orm_is_admin(message.from_user.id, session)
