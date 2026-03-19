from datetime import datetime, timezone, timedelta

import aiosqlite

from bot.config import DATABASE_PATH

PHT = timezone(timedelta(hours=8))

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS students (
    telegram_id     INTEGER PRIMARY KEY,
    full_name       TEXT    NOT NULL,
    section         TEXT    NOT NULL,
    required_hours  REAL    NOT NULL DEFAULT 486,
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS time_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id     INTEGER NOT NULL REFERENCES students(telegram_id),
    date            TEXT    NOT NULL,
    time_in         TEXT,
    time_out        TEXT,
    hours           REAL,
    created_at      TEXT    NOT NULL
);
"""


def _now() -> str:
    return datetime.now(PHT).isoformat()


async def init_db() -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.executescript(_SCHEMA)
        await db.commit()


async def get_student(telegram_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM students WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_student(
    telegram_id: int,
    full_name: str,
    section: str,
    required_hours: float,
) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO students (telegram_id, full_name, section, required_hours, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (telegram_id, full_name, section, required_hours, _now()),
        )
        await db.commit()
