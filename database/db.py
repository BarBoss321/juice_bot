import aiosqlite
from config import DB_PATH


async def get_db():
    return await aiosqlite.connect(DB_PATH)


async def init_db():
    db = await get_db()

    await db.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    await db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER UNIQUE NOT NULL,
        first_name TEXT,
        last_name TEXT,
        username TEXT,
        role TEXT NOT NULL DEFAULT 'bartender',
        company_id INTEGER NULL,
        FOREIGN KEY (company_id) REFERENCES companies(id)
    )
    """)

    await db.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        company_id INTEGER NOT NULL,
        fruit TEXT NOT NULL,
        raw REAL NOT NULL,
        juice REAL NOT NULL,
        waste REAL NOT NULL,
        percent REAL NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (company_id) REFERENCES companies(id)
    )
    """)

    # ✅ Архив отчётов (храним по месяцам)
    await db.execute("""
    CREATE TABLE IF NOT EXISTS reports_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        company_id INTEGER NOT NULL,
        fruit TEXT NOT NULL,
        raw REAL NOT NULL,
        juice REAL NOT NULL,
        waste REAL NOT NULL,
        percent REAL NOT NULL,
        created_at TEXT NOT NULL,
        archived_month TEXT NOT NULL, -- YYYY-MM
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (company_id) REFERENCES companies(id)
    )
    """)

    # ✅ Мета-таблица для служебных значений
    await db.execute("""
    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    await db.commit()
    await db.close()