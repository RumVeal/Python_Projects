from aiogram import Router, types, F
from aiogram.filters import Command
from keyboards.menu import shop_menu

router = Router()

@router.message(Command("shop"))
async def cmd_shop(message: types.Message):
    await message.answer(
        "Вот наши популярные категории:",
        reply_markup=shop_menu()
    )

@router.message(F.text == "💄 Помады")
async def lipstick_category(message: types.Message):
    await message.answer("Вы выбрали категорию '💄 Помады'. Вот наши лучшие предложения")