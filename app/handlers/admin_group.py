from aiogram import Router, types, Bot
from aiogram.filters import Command

from app.filters.check_admin import IsAdmin
from app.filters.check_chat_type import ChatTypeFilter

router = Router()
router.message.filter(IsAdmin(), ChatTypeFilter(['group', 'supergroup']))

@router.message(Command('get_chat_id'))
async def get_chat_id(message: types.Message):
    chat_id = message.chat.id
    await message.reply(f"Chat ID цієї групи: {chat_id}")

@router.message(Command('answer'))
async def answer_handler(message: types.Message, bot: Bot):
    try:
        _, user_id, *text = message.text.split(maxsplit=2)
        user_id = int(user_id)
        text = " ".join(text)

        await bot.send_message(chat_id=user_id, text=f'<b>Відповідь на ваше запитання</b>\n\n<blockquote>{text}</blockquote>')
        await message.reply("Повідомлення надіслано користувачу в приватний чат.")

    except (ValueError, IndexError):
        await message.reply("Неправильний формат команди. Використовуйте /answer <user_id> <text>")