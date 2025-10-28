from aiogram import Router, types
from aiogram.filters import Command
from keyboards.menu import shop_menu

router = Router()

@router.message(Command("shop"))
async def cmd_shop(message: types.Message):
    await message.answer(
        "Вот наши популярные категории:",
        reply_markup=shop_menu()
    )