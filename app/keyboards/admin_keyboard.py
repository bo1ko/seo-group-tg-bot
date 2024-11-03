from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


admin_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Аккаунти')],
    [KeyboardButton(text='Добавити чати'), KeyboardButton(text='Перевірка чатів')],
    # [KeyboardButton(text='Користувачі')],
    [KeyboardButton(text='Налаштування підписок')],
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

# REPLY KEYBOARDS
def get_keyboard(
    *btns: str,
    placeholder: str = None,
    request_contact: int = None,
    request_location: int = None,
    sizes: tuple[int] = (2,),
):
    '''
    Parameters request_contact and request_location must be as indexes of btns args for buttons you need.
    Example:
    get_keyboard(
            "Menu",
            "About us",
            placeholder="What do you want?",
            request_contact=4,
            sizes=(2, 2, 1)
        )
    '''
    keyboard = ReplyKeyboardBuilder()

    for index, text in enumerate(btns, start=0):
        
        if request_contact and request_contact == index:
            keyboard.add(KeyboardButton(text=text, request_contact=True))

        elif request_location and request_location == index:
            keyboard.add(KeyboardButton(text=text, request_location=True))
        else:
            keyboard.add(KeyboardButton(text=text))

    return keyboard.adjust(*sizes).as_markup(
        resize_keyboard=True, input_field_placeholder=placeholder)