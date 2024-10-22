from aiogram import Router, types
from aiogram.filters import Command

from app.filters.check_admin import IsAdmin

router = Router()
router.message.filter(IsAdmin())


# admin /admin
@router.message(Command('admin'))
async def cmd_admin(message: types.Message):
    await message.answer('Hello, admin!')
