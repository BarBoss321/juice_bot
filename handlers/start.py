from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from services.users import  register_or_update_user
from database.db import get_db
from services.roles import is_admin
from keyboards.inline import main_menu

router = Router()


@router.message(Command("s"))
async def cmd_start(message: Message):
    await register_or_update_user(message.from_user)
    tg_id = message.from_user.id
    username = message.from_user.full_name

    db = await get_db()

    # Проверяем существует ли пользователь
    cursor = await db.execute(
        "SELECT role, company_id FROM users WHERE tg_id = ?",
        (tg_id,)
    )
    user = await cursor.fetchone()

    # Если пользователя нет — создаём bartender
    if not user:
        await db.execute(
            "INSERT INTO users (tg_id, role) VALUES (?, ?)",
            (tg_id, "bartender")
        )
        await db.commit()

        text = (
            f"👋 Добро пожаловать, {username}!\n\n"
            "Вы зарегистрированы как бармен.\n"
            "⚠️ Для отправки отчётов администратор должен привязать вас к юр. лицу."
        )

    else:
        role = user[0]
        company_id = user[1]

        # Получаем название компании если привязан
        company_name = None

        if company_id:
            cursor = await db.execute(
                "SELECT name FROM companies WHERE id = ?",
                (company_id,)
            )
            company = await cursor.fetchone()
            if company:
                company_name = company[0]

        text = f"👋 С возвращением, {username}!\n\n"

        if role == "admin":
            text += "👑 Ваша роль: Администратор\n"
        else:
            text += "🥤 Ваша роль: Бармен\n"

        if company_name:
            text += f"🏢 Юр. лицо: {company_name}"
        else:
            text += "⚠️ Вы не привязаны к юр. лицу"

    await db.close()

    admin = await is_admin(tg_id)

    await message.answer(
        text,
        reply_markup=main_menu(admin)
    )