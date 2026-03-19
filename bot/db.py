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

CREATE UNIQUE INDEX IF NOT EXISTS idx_time_logs_student_date
    ON time_logs(telegram_id, date);
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


async def create_time_in(telegram_id: int) -> str | None:
    """Insert a new time_log row with the current PHT timestamp as time_in.

    Uses INSERT OR IGNORE so a concurrent duplicate is silently rejected
    by the UNIQUE index on (telegram_id, date).

    Returns the recorded time_in value, or None if a row already existed.
    """
    now = _now()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT OR IGNORE INTO time_logs (telegram_id, date, time_in, created_at) "
            "VALUES (?, ?, ?, ?)",
            (telegram_id, _today(), now, now),
        )
        await db.commit()
        if cursor.rowcount == 0:
            return None
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


async def get_todays_completed_logs() -> list[dict]:
    """Return today's completed sessions joined with student info."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT s.full_name, s.section, t.hours "
            "FROM time_logs t JOIN students s ON t.telegram_id = s.telegram_id "
            "WHERE t.date = ? AND t.hours IS NOT NULL "
            "ORDER BY s.section, s.full_name",
            (_today(),),
        )
        return [dict(r) for r in await cursor.fetchall()]


async def get_students_missing_today() -> list[dict]:
    """Return registered students with no time_log row for today."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT full_name, section FROM students "
            "WHERE telegram_id NOT IN ("
            "  SELECT telegram_id FROM time_logs WHERE date = ?"
            ") ORDER BY section, full_name",
            (_today(),),
        )
        return [dict(r) for r in await cursor.fetchall()]


async def find_student_by_name(name: str) -> dict | None:
    """Case-insensitive search for a student by full name."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM students WHERE full_name LIKE ? LIMIT 1",
            (f"%{name}%",),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_student_logs(telegram_id: int) -> list[dict]:
    """Return all time_log rows for a student, newest first."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT date, time_in, time_out, hours FROM time_logs "
            "WHERE telegram_id = ? ORDER BY date DESC",
            (telegram_id,),
        )
        return [dict(r) for r in await cursor.fetchall()]


async def get_open_sessions_today() -> list[int]:
    """Return telegram_ids that have a time_in but no time_out today."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT telegram_id FROM time_logs "
            "WHERE date = ? AND time_in IS NOT NULL AND time_out IS NULL",
            (_today(),),
        )
        return [row[0] for row in await cursor.fetchall()]


async def get_students_without_timein_today() -> list[int]:
    """Return telegram_ids of students who have not timed in today."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT telegram_id FROM students "
            "WHERE telegram_id NOT IN ("
            "  SELECT telegram_id FROM time_logs WHERE date = ?"
            ")",
            (_today(),),
        )
        return [row[0] for row in await cursor.fetchall()]
