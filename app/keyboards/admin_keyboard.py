from aiogram.types import KeyboardButton, InlineKeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup

admin_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Аккаунт')],
    [KeyboardButton(text='Добавити чати')],
    [KeyboardButton(text='Запусти ти провірку чатів')],
    [KeyboardButton(text='Добавити ключові слова')],
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
    [KeyboardButton(text='Список аккаунтів')],
    [KeyboardButton(text='Видалити аккаунт')],
    [KeyboardButton(text='Назад')],
], resize_keyboard=True, input_field_placeholder='Виберіть пункт меню...')

