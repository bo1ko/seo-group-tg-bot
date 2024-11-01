from aiogram.filters import Filter
from aiogram.types import Message

from app.database.orm_query import orm_is_sub_user


class IsSubUser(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message):
        return await orm_is_sub_user(str(message.from_user.id))
