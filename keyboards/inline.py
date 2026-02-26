from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


FRUITS = ["Апельсин", "Грейпфрут", "Лимон"]


def main_menu(is_admin: bool = False):
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить отчёт", callback_data="add_report")]
    ]

    if is_admin:
        buttons.append([InlineKeyboardButton(text="📊 Отчёт за месяц", callback_data="month_report")])
        buttons.append([InlineKeyboardButton(text="⚙️ Админ панель", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def fruit_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=fruit, callback_data=f"fruit_{fruit}")]
            for fruit in FRUITS
        ] + [[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]]
    )


def cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]]
    )


def admin_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
            [InlineKeyboardButton(text="♻️ Сбросить данные", callback_data="admin_reset")],
            [InlineKeyboardButton(text="📦 Архив", callback_data="admin_archive")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
        ]
    )


# ---------- Admin: Users ----------

def admin_users_kb(users):
    keyboard = []

    for tg_id, first_name, last_name, username, role, company in users:
        name = ""

        if first_name:
            name += first_name
        if last_name:
            name += f" {last_name}"

        name = name.strip()

        if not name:
            name = "Без имени"

        if username:
            name += f" (@{username})"

        keyboard.append([
            InlineKeyboardButton(
                text=f"{name} • {company}",
                callback_data=f"admin_user:{tg_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def admin_user_card_kb(tg_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏢 Назначить юр.лицо", callback_data=f"admin_user_set_company:{tg_id}")],
        [InlineKeyboardButton(text="🗑 Снять юр.лицо", callback_data=f"admin_user_unset_company:{tg_id}")],
        [InlineKeyboardButton(text="⬅️ К списку", callback_data="admin_users")]
    ])


def admin_companies_kb(tg_id: int, companies: list[tuple[int, str]]):
    keyboard = []
    for cid, name in companies:
        keyboard.append([InlineKeyboardButton(
            text=name,
            callback_data=f"admin_user_company:{tg_id}:{cid}"
        )])
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_user:{tg_id}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def confirm_delete_user_kb(tg_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"admin_user_delete_confirm:{tg_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"admin_user:{tg_id}")]
    ])


# ---------- Admin report: choose company ----------
def report_companies_kb(companies: list[tuple[int, str]]):
    keyboard = []
    for cid, name in companies:
        keyboard.append([InlineKeyboardButton(text=name, callback_data=f"report_company:{cid}")])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def report_result_kb(is_admin: bool = False):
    # Клава, которая показывается после успешного сохранения отчёта
    # "Отмена" здесь НЕ нужна
    buttons = [
        [InlineKeyboardButton(text="➕ Ещё отчёт", callback_data="add_report")],
    ]

    if not is_admin:
        buttons.append([InlineKeyboardButton(text="📊 Мой сегодняшний итог", callback_data="today_stats")])

    buttons.append([InlineKeyboardButton(text="🏠 В меню", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def today_stats_kb(is_admin: bool = False):
    # Клава под итогом (можно быстро добавить новый отчёт или вернуться в меню)
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить отчёт", callback_data="add_report")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_admin_reset_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, сбросить", callback_data="admin_reset_confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel")]
    ])

def archive_months_kb(months: list[str]):
    buttons = []

    for m in months:
        buttons.append(
            [InlineKeyboardButton(text=m, callback_data=f"archive_month:{m}")]
        )

    buttons.append(
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def archive_back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К архиву", callback_data="admin_archive")]
    ])