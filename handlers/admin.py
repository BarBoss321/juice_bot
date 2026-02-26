from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.reports import get_archive_months, get_archive_stats
from keyboards.inline import archive_months_kb, archive_back_kb

from keyboards.inline import (
    admin_menu,
    main_menu,
    admin_users_kb,
    admin_user_card_kb,
    admin_companies_kb,
    confirm_delete_user_kb
)
from services.roles import is_admin
from services.users import (
    list_users,
    get_user_by_tg_id,
    list_companies,
    set_user_company,
    delete_user,
    user_has_reports
)
from utils.ui import safe_edit_text
from services.users import unset_user_company
from services.maintenance import ensure_monthly_rollover, manual_reset_all_reports
from keyboards.inline import confirm_admin_reset_kb

router = Router()


@router.callback_query(F.data == "admin_reset")
async def admin_reset(callback: CallbackQuery):
    await callback.answer()

    if not await is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await ensure_monthly_rollover()

    await safe_edit_text(
        callback.message,
        "♻️ <b>Сброс данных</b>\n\n"
        "Это перенесёт текущие отчёты в архив и очистит данные текущего месяца.\n"
        "В архиве хранится максимум 2 последних месяца.\n\n"
        "Продолжить?",
        reply_markup=confirm_admin_reset_kb()
    )


@router.callback_query(F.data == "admin_reset_confirm")
async def admin_reset_confirm(callback: CallbackQuery):
    await callback.answer()

    if not await is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await manual_reset_all_reports()

    await safe_edit_text(
        callback.message,
        "✅ <b>Готово</b>\n\nДанные текущего месяца сброшены, архив обновлён.",
        reply_markup=admin_menu()
    )

@router.callback_query(F.data == "admin_panel")
async def open_admin(callback: CallbackQuery):
    await callback.answer()

    if not await is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await safe_edit_text(
        callback.message,
        "⚙️ Админ панель:",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery):
    await callback.answer()
    admin = await is_admin(callback.from_user.id)

    await safe_edit_text(
        callback.message,
        "Главное меню:",
        reply_markup=main_menu(admin)
    )


@router.callback_query(F.data == "admin_users")
async def show_users(callback: CallbackQuery):
    await callback.answer()

    if not await is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    users = await list_users()
    await safe_edit_text(
        callback.message,
        "👥 Пользователи (выберите):",
        reply_markup=admin_users_kb(users)
    )


@router.callback_query(F.data.startswith("admin_user:"))
async def user_card(callback: CallbackQuery):
    await callback.answer()

    if not await is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    tg_id = int(callback.data.split(":")[1])
    user = await get_user_by_tg_id(tg_id)

    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    tg_id, role, company_id, company_name = user
    company_name = company_name if company_name else "Не привязан"

    text = (
        "👤 Карточка пользователя\n\n"
        f"TG ID: {tg_id}\n"
        f"Роль: {role}\n"
        f"Юр.лицо: {company_name}\n"
    )

    await safe_edit_text(
        callback.message,
        text,
        reply_markup=admin_user_card_kb(tg_id)
    )

    @router.callback_query(F.data.startswith("admin_user_set_company:"))
    async def user_set_company(callback: CallbackQuery):
        await callback.answer()

        if not await is_admin(callback.from_user.id):
            await callback.answer("Нет доступа", show_alert=True)
            return

        tg_id = int(callback.data.split(":")[1])
        companies = await list_companies()

        await safe_edit_text(
            callback.message,
            f"🏢 Выберите юр.лицо для пользователя {tg_id}:",
            reply_markup=admin_companies_kb(tg_id, companies)
        )

    @router.callback_query(F.data.startswith("admin_user_unset_company:"))
    async def user_unset_company(callback: CallbackQuery):
        await callback.answer()

        if not await is_admin(callback.from_user.id):
            await callback.answer("Нет доступа", show_alert=True)
            return

        tg_id = int(callback.data.split(":")[1])
        await unset_user_company(tg_id)

        user = await get_user_by_tg_id(tg_id)
        company_name = user[3] if user and user[3] else "Не привязан"

        text = (
            "✅ Юр.лицо снято\n\n"
            f"TG ID: {tg_id}\n"
            f"Юр.лицо: {company_name}\n"
        )

        await safe_edit_text(
            callback.message,
            text,
            reply_markup=admin_user_card_kb(tg_id)
        )

    @router.callback_query(F.data.startswith("admin_user_company:"))
    async def user_choose_company(callback: CallbackQuery):
        await callback.answer()

        if not await is_admin(callback.from_user.id):
            await callback.answer("Нет доступа", show_alert=True)
            return

        parts = callback.data.split(":")
        # ожидаем: admin_user_company:<tg_id>:<company_id>
        if len(parts) != 3:
            await callback.answer("Некорректные данные кнопки", show_alert=True)
            return

        _, tg_id_str, company_id_str = parts
        tg_id = int(tg_id_str)
        company_id = int(company_id_str)

        await set_user_company(tg_id, company_id)

        # возвращаемся в карточку пользователя
        user = await get_user_by_tg_id(tg_id)
        company_name = user[3] if user and user[3] else "Не привязан"

        text = (
            "✅ Юр.лицо назначено\n\n"
            f"TG ID: {tg_id}\n"
            f"Юр.лицо: {company_name}\n"
        )

        await safe_edit_text(
            callback.message,
            text,
            reply_markup=admin_user_card_kb(tg_id)
        )

    @router.callback_query(F.data.startswith("admin_user_delete:"))
    async def user_delete_ask(callback: CallbackQuery):
        await callback.answer()

        if not await is_admin(callback.from_user.id):
            await callback.answer("Нет доступа", show_alert=True)
            return

        tg_id = int(callback.data.split(":")[1])

        await safe_edit_text(
            callback.message,
            f"🗑 Точно удалить пользователя {tg_id}?",
            reply_markup=confirm_delete_user_kb(tg_id)
        )

        @router.callback_query(F.data.startswith("admin_user_delete_confirm:"))
        async def user_delete_confirm(callback: CallbackQuery):
            await callback.answer()

            if not await is_admin(callback.from_user.id):
                await callback.answer("Нет доступа", show_alert=True)
                return

            tg_id = int(callback.data.split(":")[1])

            # защита: если есть отчёты — не удаляем, чтобы не ломать историю
            if await user_has_reports(tg_id):
                await callback.answer("Нельзя удалить: у пользователя есть отчёты", show_alert=True)
                # вернём в карточку
                await user_card(
                    CallbackQuery(**{**callback.model_dump(), "data": f"admin_user:{tg_id}"}))  # безопасно не всегда
                return

            await delete_user(tg_id)

            users = await list_users()
            await safe_edit_text(
                callback.message,
                "✅ Пользователь удалён.\n\n👥 Пользователи (выберите):",
                reply_markup=admin_users_kb(users)
            )

        @router.callback_query(F.data.startswith("admin_user_delete_confirm:"))
        async def user_delete_confirm(callback: CallbackQuery):
            await callback.answer()

            if not await is_admin(callback.from_user.id):
                await callback.answer("Нет доступа", show_alert=True)
                return

            tg_id = int(callback.data.split(":")[1])

            # защита: если есть отчёты — не удаляем, чтобы не ломать историю
            if await user_has_reports(tg_id):
                await callback.answer("Нельзя удалить: у пользователя есть отчёты", show_alert=True)
                # вернём в карточку
                await user_card(
                    CallbackQuery(**{**callback.model_dump(), "data": f"admin_user:{tg_id}"}))  # безопасно не всегда
                return

            await delete_user(tg_id)

            users = await list_users()
            await safe_edit_text(
                callback.message,
                "✅ Пользователь удалён.\n\n👥 Пользователи (выберите):",
                reply_markup=admin_users_kb(users)
            )

@router.callback_query(F.data == "admin_archive")
async def admin_archive(callback: CallbackQuery):
    await callback.answer()

    if not await is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    months = await get_archive_months()

    if not months:
        await safe_edit_text(
            callback.message,
            "📦 <b>Архив</b>\n\nНет сохранённых месяцев",
            reply_markup=admin_menu()
        )
        return

    await safe_edit_text(
        callback.message,
        "📦 <b>Выберите месяц:</b>",
        reply_markup=archive_months_kb(months)
    )

@router.callback_query(F.data.startswith("archive_month:"))
async def archive_month(callback: CallbackQuery):
    await callback.answer()

    if not await is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    month = callback.data.split(":")[1]
    text = await get_archive_stats(month)

    await safe_edit_text(
        callback.message,
        text,
        reply_markup=archive_back_kb()
    )