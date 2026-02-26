from database.db import get_db
from services.roles import get_user


async def add_report(tg_id: int, fruit: str, raw: float, juice: float, waste: float, company_id_override: int | None = None):
    user = await get_user(tg_id)
    if not user:
        return

    user_id = user[0]
    user_company_id = user[2]

    company_id = company_id_override if company_id_override is not None else user_company_id
    if company_id is None:
        return

    percent = round((juice / raw) * 100, 2) if raw else 0

    db = await get_db()
    await db.execute(
        """
        INSERT INTO reports (user_id, company_id, fruit, raw, juice, waste, percent)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, company_id, fruit, raw, juice, waste, percent)
    )
    await db.commit()
    await db.close()


async def get_month_stats():
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT c.name, r.fruit,
               SUM(r.raw)  AS total_raw,
               SUM(r.juice) AS total_juice,
               SUM(r.waste) AS total_waste
        FROM reports r
        JOIN companies c ON r.company_id = c.id
        WHERE strftime('%Y-%m', r.created_at) = strftime('%Y-%m', 'now')
        GROUP BY c.name, r.fruit
        ORDER BY c.name, r.fruit
        """
    )
    rows = await cursor.fetchall()
    await db.close()

    if not rows:
        return "Нет данных"

    text = "📊 <b>Отчёт за месяц</b>\n"
    current_company = None

    for company, fruit, total_raw, total_juice, total_waste in rows:
        total_raw = float(total_raw or 0)
        total_juice = float(total_juice or 0)
        total_waste = float(total_waste or 0)

        juice_percent = round((total_juice / total_raw) * 100, 2) if total_raw else 0
        waste_percent = round((total_waste / total_raw) * 100, 2) if total_raw else 0

        if company != current_company:
            text += f"\n\n🏢 <b>{company}</b>\n"
            text += "──────────────\n"
            current_company = company

        text += (
            f"\n🍊 <b>{fruit}</b>\n"
            f"<code>Сырьё : {total_raw:.0f} г</code>\n"
            f"<code>Сок   : {total_juice:.0f} г ({juice_percent}%)</code>\n"
            f"<code>Отход : {total_waste:.0f} г ({waste_percent}%)</code>\n"
        )

    return text

async def get_today_stats_for_user(tg_id: int) -> str:
    # Итог за сегодня по компании пользователя (по фруктам)
    user = await get_user(tg_id)
    if not user:
        return "Нет данных"

    company_id = user[2]
    if company_id is None:
        return "⚠️ Вы не привязаны к юр.лицу"

    db = await get_db()
    cursor = await db.execute(
        """
        SELECT c.name, r.fruit,
               SUM(r.raw)  AS total_raw,
               SUM(r.juice) AS total_juice,
               SUM(r.waste) AS total_waste
        FROM reports r
        JOIN companies c ON r.company_id = c.id
        WHERE r.company_id = ?
          AND date(r.created_at) = date('now')
        GROUP BY c.name, r.fruit
        ORDER BY r.fruit
        """,
        (company_id,)
    )
    rows = await cursor.fetchall()
    await db.close()

    if not rows:
        return "📊 <b>Сегодня</b>\n\nНет данных за сегодня"

    company_name = rows[0][0]
    text = f"📊 <b>Сегодня</b>\n🏢 <b>{company_name}</b>\n"

    for _, fruit, total_raw, total_juice, total_waste in rows:
        total_raw = float(total_raw or 0)
        total_juice = float(total_juice or 0)
        total_waste = float(total_waste or 0)

        juice_percent = round((total_juice / total_raw) * 100, 2) if total_raw else 0
        waste_percent = round((total_waste / total_raw) * 100, 2) if total_raw else 0

        text += (
            f"\n🍊 <b>{fruit}</b>\n"
            f"<code>Сырьё : {total_raw:.0f} г</code>\n"
            f"<code>Сок   : {total_juice:.0f} г ({juice_percent}%)</code>\n"
            f"<code>Отход : {total_waste:.0f} г ({waste_percent}%)</code>\n"
        )

    return text

async def get_archive_months() -> list[str]:
    db = await get_db()
    cursor = await db.execute("""
        SELECT archived_month
        FROM reports_archive
        GROUP BY archived_month
        ORDER BY archived_month DESC
    """)
    rows = await cursor.fetchall()
    await db.close()

    return [r[0] for r in rows]


async def get_archive_stats(month: str) -> str:
    db = await get_db()
    cursor = await db.execute("""
        SELECT c.name, r.fruit,
               SUM(r.raw),
               SUM(r.juice),
               SUM(r.waste)
        FROM reports_archive r
        JOIN companies c ON r.company_id = c.id
        WHERE r.archived_month = ?
        GROUP BY c.name, r.fruit
        ORDER BY c.name, r.fruit
    """, (month,))
    rows = await cursor.fetchall()
    await db.close()

    if not rows:
        return f"📦 <b>Архив {month}</b>\n\nНет данных"

    text = f"📦 <b>Архив {month}</b>\n"
    current_company = None

    for company, fruit, raw, juice, waste in rows:
        raw = float(raw or 0)
        juice = float(juice or 0)
        waste = float(waste or 0)

        juice_percent = round((juice / raw) * 100, 2) if raw else 0
        waste_percent = round((waste / raw) * 100, 2) if raw else 0

        if company != current_company:
            text += f"\n\n🏢 <b>{company}</b>\n──────────────"
            current_company = company

        text += (
            f"\n\n🍊 <b>{fruit}</b>\n"
            f"<code>Сырьё : {raw:.0f} г</code>\n"
            f"<code>Сок   : {juice:.0f} г ({juice_percent}%)</code>\n"
            f"<code>Отход : {waste:.0f} г ({waste_percent}%)</code>\n"
        )

    return text