from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


main_placeholder = 'Виберіть пункт меню...'

user_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Ключові слова 🔑')],
    [KeyboardButton(text='Інформація про підписку 🔥')],
    [KeyboardButton(text="Зв'язок з адміністратором 📱")],
], resize_keyboard=True, input_field_placeholder=main_placeholder)

keywords = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Список ключових слів')],
    [KeyboardButton(text='Додати ключові слова')],
    [KeyboardButton(text='Видалити ключові слова')],
    [KeyboardButton(text='Головне меню')],
], resize_keyboard=True, input_field_placeholder=main_placeholder)

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Головне меню')]
], resize_keyboard=True, input_field_placeholder=main_placeholder)

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