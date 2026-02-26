from database.db import get_db


async def list_users():
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT 
            u.tg_id,
            u.first_name,
            u.last_name,
            u.username,
            u.role,
            COALESCE(c.name, 'Не привязан') as company
        FROM users u
        LEFT JOIN companies c ON u.company_id = c.id
        ORDER BY u.id DESC
        """
    )
    rows = await cursor.fetchall()
    await db.close()
    return rows


async def get_user_by_tg_id(tg_id: int):
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT u.tg_id, u.role, u.company_id, c.name
        FROM users u
        LEFT JOIN companies c ON u.company_id = c.id
        WHERE u.tg_id = ?
        """,
        (tg_id,)
    )
    row = await cursor.fetchone()
    await db.close()
    return row


async def list_companies():
    db = await get_db()
    cursor = await db.execute("SELECT id, name FROM companies ORDER BY id")
    rows = await cursor.fetchall()
    await db.close()
    return rows


async def set_user_company(tg_id: int, company_id: int):
    db = await get_db()
    await db.execute("UPDATE users SET company_id = ? WHERE tg_id = ?", (company_id, tg_id))
    await db.commit()
    await db.close()


async def user_has_reports(tg_id: int) -> bool:
    db = await get_db()
    # reports.user_id хранит внутренний users.id, поэтому делаем join
    cursor = await db.execute(
        """
        SELECT 1
        FROM reports r
        JOIN users u ON u.id = r.user_id
        WHERE u.tg_id = ?
        LIMIT 1
        """,
        (tg_id,)
    )
    row = await cursor.fetchone()
    await db.close()
    return row is not None


async def delete_user(tg_id: int):
    db = await get_db()
    await db.execute("DELETE FROM users WHERE tg_id = ?", (tg_id,))
    await db.commit()
    await db.close()

async def unset_user_company(tg_id: int):
    db = await get_db()
    await db.execute("UPDATE users SET company_id = NULL WHERE tg_id = ?", (tg_id,))
    await db.commit()
    await db.close()

async def register_or_update_user(tg_user):
    db = await get_db()
    await db.execute(
        """
        INSERT INTO users (tg_id, first_name, last_name, username, role)
        VALUES (?, ?, ?, ?, 'bartender')
        ON CONFLICT(tg_id) DO UPDATE SET
            first_name=excluded.first_name,
            last_name=excluded.last_name,
            username=excluded.username
        """,
        (tg_user.id, tg_user.first_name, tg_user.last_name, tg_user.username)
    )
    await db.commit()
    await db.close()