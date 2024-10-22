from aiogram import Router, types
from aiogram.filters import CommandStart

router = Router()


#  /start
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer('Вітаю!')
