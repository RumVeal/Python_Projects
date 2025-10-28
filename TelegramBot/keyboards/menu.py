from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Магазин"), KeyboardButton(text="📦 Мои заказы")],
            [KeyboardButton(text="ℹ️ О нас")]
        ],
        resize_keyboard=True
    )

def shop_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
        [KeyboardButton(text="💄 Помады"), KeyboardButton(text="🧴 Кремы")],
        [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )