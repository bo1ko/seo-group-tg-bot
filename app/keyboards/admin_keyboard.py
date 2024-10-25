from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

admin_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Аккаунт'), KeyboardButton(text='Ключові слова')],
    [KeyboardButton(text='Добавити чати'), KeyboardButton(text='Перевірка чатів')],
    # [KeyboardButton(text='Користувачі')],
    [KeyboardButton(text='Сховати адмін меню')]
], resize_keyboard=True, input_field_placeholder='Виберіть пункт меню...')

hide_admin_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Відкрити адмін меню')]
], resize_keyboard=True, input_field_placeholder='Виберіть пункт меню...')

account_add = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Добавити аккаунт')],
    [KeyboardButton(text='Назад')],
], resize_keyboard=True, input_field_placeholder='Виберіть пункт меню...')

account_manage = ReplyKeyboardMarkup(keyboard=[
    # [KeyboardButton(text='Список аккаунтів')],
    [KeyboardButton(text='Видалити аккаунт')],
    [KeyboardButton(text='Назад')],
], resize_keyboard=True, input_field_placeholder='Виберіть пункт меню...')

keywords = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Список ключових слів')],
    [KeyboardButton(text='Додати ключові слова')],
    [KeyboardButton(text='Видалити ключові слова')],
    [KeyboardButton(text='Назад')],
], resize_keyboard=True, input_field_placeholder='Виберіть пункт меню...')

stop_add_chats = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Зупинити додавання чатів')],
    [KeyboardButton(text='Назад')],
], resize_keyboard=True, input_field_placeholder='Виберіть пункт меню...')

start_add_chats = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Запустити додавання чатів')],
    [KeyboardButton(text='Назад')],
], resize_keyboard=True, input_field_placeholder='Виберіть пункт меню...')

stop_chat_checker = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Зупинити перевірку чатів')],
    [KeyboardButton(text='Назад')],
], resize_keyboard=True, input_field_placeholder='Виберіть пункт меню...')

start_chat_checker = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Запустити перевірку чатів')],
    [KeyboardButton(text='Назад')],
], resize_keyboard=True, input_field_placeholder='Виберіть пункт меню...')

users_manage = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Список користувачів'), KeyboardButton(text='Список адміністраторів')],
    [KeyboardButton(text='Добавити користувача'), KeyboardButton(text='Додати адміністратора')],
    [KeyboardButton(text='Видалити користувача'), KeyboardButton(text='Видалити адміністратора')],
    [KeyboardButton(text='Назад')],
], resize_keyboard=True, input_field_placeholder='Виберіть пункт меню...')

back = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Назад')],
], resize_keyboard=True, input_field_placeholder='Виберіть пункт меню...')

# INLINE KEYBOARDS
def get_callback_btns(*, btns: dict[str, str], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()