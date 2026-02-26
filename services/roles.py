from database.db import get_db


async def get_user(tg_id: int):
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, role, company_id FROM users WHERE tg_id = ?",
        (tg_id,)
    )
    row = await cursor.fetchone()
    await db.close()
    return row


async def is_admin(tg_id: int):
    user = await get_user(tg_id)
    return bool(user and user[1] == "admin")


async def can_make_reports(tg_id: int):
    user = await get_user(tg_id)
    if not user:
        return False
    role = user[1]
    company_id = user[2]
    return role == "admin" or company_id is not None