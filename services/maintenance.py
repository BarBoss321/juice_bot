from database.db import get_db


def _current_month_sql() -> str:
    # YYYY-MM в SQLite
    return "strftime('%Y-%m', 'now')"


async def _get_meta(key: str) -> str | None:
    db = await get_db()
    cursor = await db.execute("SELECT value FROM meta WHERE key = ?", (key,))
    row = await cursor.fetchone()
    await db.close()
    return row[0] if row else None


async def _set_meta(key: str, value: str) -> None:
    db = await get_db()
    await db.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value)
    )
    await db.commit()
    await db.close()


async def trim_archive_keep_last_months(keep: int = 2) -> None:
    db = await get_db()

    # получаем список месяцев (по убыванию)
    cursor = await db.execute("""
        SELECT archived_month
        FROM reports_archive
        GROUP BY archived_month
        ORDER BY archived_month DESC
    """)
    months = [r[0] for r in await cursor.fetchall()]

    to_delete = months[keep:]
    if to_delete:
        await db.execute(
            f"DELETE FROM reports_archive WHERE archived_month IN ({','.join(['?'] * len(to_delete))})",
            to_delete
        )

    await db.commit()
    await db.close()


async def archive_old_reports() -> None:
    """
    Автоперекат:
    - всё, что НЕ текущий месяц из reports → reports_archive
    - reports очищаем от прошлых месяцев
    """
    db = await get_db()

    # перенести старое в архив
    await db.execute(f"""
        INSERT INTO reports_archive (user_id, company_id, fruit, raw, juice, waste, percent, created_at, archived_month)
        SELECT user_id, company_id, fruit, raw, juice, waste, percent, created_at, strftime('%Y-%m', created_at)
        FROM reports
        WHERE strftime('%Y-%m', created_at) != {_current_month_sql()}
    """)

    # удалить из основной таблицы
    await db.execute(f"""
        DELETE FROM reports
        WHERE strftime('%Y-%m', created_at) != {_current_month_sql()}
    """)

    await db.commit()
    await db.close()

    await trim_archive_keep_last_months(keep=2)


async def ensure_monthly_rollover() -> None:
    """
    Вызываем при важных действиях (add_report, month_report, admin reset).
    Если месяц сменился — делаем перекат 1 раз.
    """
    current_month = None
    db = await get_db()
    cursor = await db.execute(f"SELECT {_current_month_sql()}")
    row = await cursor.fetchone()
    await db.close()
    current_month = row[0]

    last = await _get_meta("last_rollover_month")
    if last == current_month:
        return

    # месяц новый → перекатываем старые отчёты
    await archive_old_reports()
    await _set_meta("last_rollover_month", current_month)


async def manual_reset_all_reports() -> None:
    """
    Ручной сброс админом:
    - всё, что сейчас в reports (текущий месяц) → в архив (с archived_month = текущий месяц)
    - reports очищаем полностью
    - архив держим максимум 2 месяца
    """
    db = await get_db()

    # текущий месяц
    cursor = await db.execute(f"SELECT {_current_month_sql()}")
    current_month = (await cursor.fetchone())[0]

    # переносим ВСЁ что есть в reports как снапшот текущего месяца
    await db.execute("""
        INSERT INTO reports_archive (user_id, company_id, fruit, raw, juice, waste, percent, created_at, archived_month)
        SELECT user_id, company_id, fruit, raw, juice, waste, percent, created_at, ?
        FROM reports
    """, (current_month,))

    await db.execute("DELETE FROM reports")

    await db.commit()
    await db.close()

    await trim_archive_keep_last_months(keep=2)
    await _set_meta("last_rollover_month", current_month)