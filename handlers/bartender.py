from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from services.reports import get_today_stats_for_user
from keyboards.inline import report_result_kb, today_stats_kb
from states.report_state import AddReport
from services.roles import can_make_reports, is_admin
from services.reports import add_report, get_month_stats
from services.users import list_companies
from keyboards.inline import (
    main_menu,
    cancel_keyboard,
    fruit_keyboard,
    report_companies_kb
)
from utils.ui import safe_edit_text
from services.maintenance import ensure_monthly_rollover


router = Router()


def build_breadcrumbs(data: dict, is_admin_user: bool) -> str:
    lines = ["🧾 <b>Новый отчёт</b>"]

    if is_admin_user:
        company_name = data.get("company_name")
        if company_name:
            lines.append(f"🏢 Компания: <b>{company_name}</b>")

    fruit = data.get("fruit")
    if fruit:
        lines.append(f"🍊 Фрукт: <b>{fruit}</b>")

    if "raw" in data:
        lines.append(f"⚖️ Сырьё: <b>{data['raw']}</b> г")
    if "juice" in data:
        lines.append(f"🧃 Сок: <b>{data['juice']}</b> г")

    return "\n".join(lines)


def compose_step_text(data: dict, admin_user: bool, prompt: str, error: str | None = None) -> str:
    breadcrumbs = build_breadcrumbs(data, admin_user)
    if error:
        return f"{breadcrumbs}\n\n❗️<b>Ошибка:</b> {error}\n\n{prompt}"
    return f"{breadcrumbs}\n\n{prompt}"


async def edit_menu_message(bot, chat_id: int, message_id: int, text: str, reply_markup):
    # безопасное редактирование по id (чтобы не мусорить)
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception:
        # на всякий случай не валим бота, но это редко нужно
        pass


@router.callback_query(F.data == "add_report")
async def start_add(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await ensure_monthly_rollover()

    admin_user = await is_admin(callback.from_user.id)

    if not await can_make_reports(callback.from_user.id):
        await callback.answer(
            "⚠️ Вы не привязаны к юр.лицу.\n\nОбратитесь к администратору.",
            show_alert=True
        )
        return

    if admin_user:
        companies = await list_companies()
        await state.set_state(AddReport.company)
        await safe_edit_text(
            callback.message,
            "🏢 <b>Выберите юр.лицо для отчёта:</b>",
            reply_markup=report_companies_kb(companies)
        )
        return

    await state.set_state(AddReport.fruit)
    await safe_edit_text(callback.message, "🍊 <b>Выберите фрукт:</b>", reply_markup=fruit_keyboard())


@router.callback_query(AddReport.company, F.data.startswith("report_company:"))
async def choose_company(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    company_id = int(callback.data.split(":")[1])

    companies = await list_companies()
    company_name = None
    for cid, name in companies:
        if cid == company_id:
            company_name = name
            break

    await state.update_data(company_id=company_id, company_name=company_name)

    await state.set_state(AddReport.fruit)
    await safe_edit_text(
        callback.message,
        f"🏢 Компания: <b>{company_name}</b>\n\n🍊 <b>Выберите фрукт:</b>",
        reply_markup=fruit_keyboard()
    )


@router.callback_query(F.data.startswith("fruit_"))
async def choose_fruit(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    fruit = callback.data.split("_", 1)[1]

    await state.update_data(
        fruit=fruit,
        menu_message_id=callback.message.message_id
    )

    await state.set_state(AddReport.raw)

    data = await state.get_data()
    admin_user = await is_admin(callback.from_user.id)

    text = compose_step_text(data, admin_user, "⚖️ <b>Введите сырьё (г):</b>")
    await safe_edit_text(callback.message, text, reply_markup=cancel_keyboard())


@router.message(AddReport.raw)
async def get_raw(message: Message, state: FSMContext):
    data = await state.get_data()
    admin_user = await is_admin(message.from_user.id)

    try:
        raw = float(message.text)
        if raw <= 0:
            raise ValueError
    except Exception:
        # удаляем сообщение бармена и показываем ошибку в том же меню-сообщении
        await message.delete()
        text = compose_step_text(data, admin_user, "⚖️ <b>Введите сырьё (г):</b>", "введите число больше 0")
        await edit_menu_message(message.bot, message.chat.id, data["menu_message_id"], text, cancel_keyboard())
        return

    await state.update_data(raw=raw)
    await state.set_state(AddReport.juice)

    data = await state.get_data()
    text = compose_step_text(data, admin_user, "🧃 <b>Введите сок (г):</b>")
    await edit_menu_message(message.bot, message.chat.id, data["menu_message_id"], text, cancel_keyboard())
    await message.delete()


@router.message(AddReport.juice)
async def get_juice(message: Message, state: FSMContext):
    data = await state.get_data()
    admin_user = await is_admin(message.from_user.id)

    try:
        juice = float(message.text)
        if juice < 0:
            raise ValueError
    except Exception:
        await message.delete()
        text = compose_step_text(data, admin_user, "🧃 <b>Введите сок (г):</b>", "введите число 0 или больше")
        await edit_menu_message(message.bot, message.chat.id, data["menu_message_id"], text, cancel_keyboard())
        return

    await state.update_data(juice=juice)
    await state.set_state(AddReport.waste)

    data = await state.get_data()
    text = compose_step_text(data, admin_user, "🗑 <b>Введите отход (г):</b>")
    await edit_menu_message(message.bot, message.chat.id, data["menu_message_id"], text, cancel_keyboard())
    await message.delete()


@router.message(AddReport.waste)
async def get_waste(message: Message, state: FSMContext):
    data = await state.get_data()
    admin_user = await is_admin(message.from_user.id)

    try:
        waste = float(message.text)
        if waste < 0:
            raise ValueError
    except Exception:
        await message.delete()
        text = compose_step_text(data, admin_user, "🗑 <b>Введите отход (г):</b>", "введите число 0 или больше")
        await edit_menu_message(message.bot, message.chat.id, data["menu_message_id"], text, cancel_keyboard())
        return

    raw = float(data["raw"])
    juice = float(data["juice"])

    # ❗️ошибка не мусорит чат — просто редактируем то же сообщение и ждём новое число
    if juice + waste > raw + 5:
        await message.delete()
        text = compose_step_text(
            data,
            admin_user,
            "🗑 <b>Введите отход (г):</b>",
            "сок + отход превышают сырьё более чем на 5 г. Введите верное количество."
        )
        await edit_menu_message(message.bot, message.chat.id, data["menu_message_id"], text, cancel_keyboard())
        return

    fruit = data["fruit"]
    company_id = data.get("company_id")  # для admin

    await add_report(
        tg_id=message.from_user.id,
        fruit=fruit,
        raw=raw,
        juice=juice,
        waste=waste,
        company_id_override=company_id
    )

    juice_percent = round((juice / raw) * 100, 2) if raw else 0
    waste_percent = round((waste / raw) * 100, 2) if raw else 0

    company_name = data.get("company_name")

    header = "✅ <b>Отчёт добавлен</b>\n\n"
    if admin_user and company_name:
        header += f"🏢 Компания: <b>{company_name}</b>\n"

    result_text = (
        header +
        f"🍊 Фрукт: <b>{fruit}</b>\n"
        f"<code>Сырьё : {raw:.0f} г</code>\n"
        f"<code>Сок   : {juice:.0f} г ({juice_percent}%)</code>\n"
        f"<code>Отход : {waste:.0f} г ({waste_percent}%)</code>\n"
    )

    # ✅ ВАЖНО: финал — редактируем то же меню-сообщение
    # и ставим main_menu => "Отмена" исчезает
    await edit_menu_message(
        message.bot,
        message.chat.id,
        data["menu_message_id"],
        result_text,
        report_result_kb(admin_user)
    )

    await state.clear()
    await message.delete()


@router.callback_query(F.data == "month_report")
async def month_report(callback: CallbackQuery):
    await callback.answer()
    await ensure_monthly_rollover()

    if not await is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    stats = await get_month_stats()
    await safe_edit_text(callback.message, stats, reply_markup=main_menu(True))


@router.callback_query(F.data == "cancel")
async def cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

    admin_user = await is_admin(callback.from_user.id)
    await safe_edit_text(callback.message, "Главное меню:", reply_markup=main_menu(admin_user))

@router.callback_query(F.data == "today_stats")
async def today_stats(callback: CallbackQuery):
    await callback.answer()

    # только для барменов (для админа мы кнопку не показываем, но на всякий случай)
    if await is_admin(callback.from_user.id):
        await callback.answer("Недоступно", show_alert=True)
        return

    text = await get_today_stats_for_user(callback.from_user.id)
    await safe_edit_text(
        callback.message,
        text,
        reply_markup=today_stats_kb(False)
    )