from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from services.roles import is_admin

async def get_main_keyboard(user_id: int):

    buttons = [
        [KeyboardButton(text="➕ Добавить запись")],
        [KeyboardButton(text="📅 Отчёт за день")],
        [KeyboardButton(text="📊 Отчёт за месяц")]
    ]

    # если админ — добавляем кнопку
    if await is_admin(user_id):
        buttons.append([KeyboardButton(text="⚙️ Админка")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )