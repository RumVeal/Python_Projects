import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import TOKEN
from handlers import start, shop

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="shop", description="Открыть магазин"),
    ]
    await bot.set_my_commands(commands)

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    dp.include_router(start.router)
    dp.include_router(shop.router)
    
    await set_commands(bot)
    print("Bot is starting...")
    
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())