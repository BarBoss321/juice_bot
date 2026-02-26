import asyncio
from aiogram import Bot, Dispatcher

from config import TOKEN
from database.db import init_db

from handlers import start, bartender, admin


async def main():
    bot = Bot(TOKEN)
    dp = Dispatcher()

    await init_db()

    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(bartender.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())