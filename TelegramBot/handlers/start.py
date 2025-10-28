from aiogram import Router, types
from aiogram.filters import Command
from keyboards.menu import main_menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! 👋 Добро пожаловать в наш магазин корейской косметики!\n"
        "Выбери нужный раздел ниже 👇",
        reply_markup=main_menu()
    )