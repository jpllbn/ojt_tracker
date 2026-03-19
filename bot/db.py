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


def _today() -> str:
    return datetime.now(PHT).strftime("%Y-%m-%d")


async def get_today_log(telegram_id: int) -> dict | None:
    """Return today's time_log row for the student, or None."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM time_logs WHERE telegram_id = ? AND date = ?",
            (telegram_id, _today()),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_time_in(telegram_id: int) -> str:
    """Insert a new time_log row with the current PHT timestamp as time_in.

    Returns the recorded time_in value.
    """
    now = _now()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO time_logs (telegram_id, date, time_in, created_at) "
            "VALUES (?, ?, ?, ?)",
            (telegram_id, _today(), now, now),
        )
        await db.commit()
    return now


async def update_time_out(log_id: int, time_in_iso: str) -> tuple[str, float] | None:
    """Set time_out and compute hours for an existing log row.

    The UPDATE is guarded by ``time_out IS NULL`` so a concurrent request
    that arrives after the first commit becomes a no-op.

    Returns (time_out_iso, hours_worked), or None if the row was already
    closed by a concurrent request.
    """
    now_dt = datetime.now(PHT)
    time_in_dt = datetime.fromisoformat(time_in_iso)
    hours = round((now_dt - time_in_dt).total_seconds() / 3600, 2)
    now_iso = now_dt.isoformat()

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "UPDATE time_logs SET time_out = ?, hours = ? "
            "WHERE id = ? AND time_out IS NULL",
            (now_iso, hours, log_id),
        )
        await db.commit()
        if cursor.rowcount == 0:
            return None
    return now_iso, hours


async def get_total_hours(telegram_id: int) -> float:
    """Sum all completed session hours for the student."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT COALESCE(SUM(hours), 0) FROM time_logs "
            "WHERE telegram_id = ? AND hours IS NOT NULL",
            (telegram_id,),
        )
        row = await cursor.fetchone()
        return float(row[0])
