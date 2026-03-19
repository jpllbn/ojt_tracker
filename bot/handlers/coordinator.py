from datetime import datetime
import re

from telegram import Update
from telegram.ext import ContextTypes

from bot import db
from bot.handlers.common import coordinator_only

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _fmt_time(iso: str | None) -> str:
    if not iso:
        return "—"
    return datetime.fromisoformat(iso).strftime("%I:%M %p")


@coordinator_only
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logs = await db.get_todays_completed_logs()

    if not logs:
        await update.message.reply_text("No students have completed a log today.")
        return

    lines = [f"Completed logs for today ({len(logs)}):\n"]
    for i, log in enumerate(logs, 1):
        lines.append(
            f"{i}. {log['full_name']} ({log['section']}) — {log['hours']} hrs"
        )

    await update.message.reply_text("\n".join(lines))


@coordinator_only
async def missing_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    students = await db.get_students_missing_today()

    if not students:
        await update.message.reply_text("All registered students have logged today.")
        return

    lines = [f"Students with no log today ({len(students)}):\n"]
    for i, s in enumerate(students, 1):
        lines.append(f"{i}. {s['full_name']} ({s['section']})")

    await update.message.reply_text("\n".join(lines))


@coordinator_only
async def hours_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await update.message.reply_text(
            "Please provide a student name.\n"
            "Example: /hours Ana Reyes"
        )
        return

    name = " ".join(args).lstrip("@")
    student = await db.find_student_by_name(name)

    if not student:
        await update.message.reply_text(
            f'No registered student matches "{name}".'
        )
        return

    logs = await db.get_student_logs(student["telegram_id"])
    leaves = await db.get_student_leaves(student["telegram_id"])
    total = await db.get_total_hours(student["telegram_id"])

    header = (
        f"{student['full_name']} ({student['section']})\n"
        f"Required: {student['required_hours']} hrs | "
        f"Rendered: {total} hrs\n"
    )

    if not logs and not leaves:
        await update.message.reply_text(header + "\nNo sessions recorded yet.")
        return

    leave_map = {lv["date"]: lv["reason"] for lv in leaves}

    lines = [header, "Date       | In       | Out      | Hours"]
    for log in logs:
        hrs = log["hours"] if log["hours"] is not None else "\u2014"
        lines.append(
            f"{log['date']} | {_fmt_time(log['time_in'])} | "
            f"{_fmt_time(log['time_out'])} | {hrs}"
        )

    corrected_ids = await db.get_corrections_for_student(student["telegram_id"])

    for date, reason in sorted(leave_map.items(), reverse=True):
        if date not in {log["date"] for log in logs}:
            lines.append(f"{date} | LEAVE: {reason}")

    for log in logs:
        if log.get("id") and log["id"] in corrected_ids:
            idx = next(
                (i for i, ln in enumerate(lines) if ln.startswith(log["date"])),
                None,
            )
            if idx is not None:
                lines[idx] += " *"

    await update.message.reply_text("\n".join(lines))


@coordinator_only
async def correct_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> None:
    args = context.args
    if not args or len(args) < 3:
        await update.message.reply_text(
            "Usage: /correct <studentname> <date> <hours>\n"
            "Example: /correct Ana Reyes 2026-03-19 8.5"
        )
        return

    hours_str = args[-1]
    date_str = args[-2]
    name = " ".join(args[:-2]).lstrip("@")

    if not _DATE_RE.match(date_str):
        await update.message.reply_text(
            f'Invalid date format "{date_str}". Use YYYY-MM-DD.'
        )
        return

    try:
        new_hours = round(float(hours_str), 2)
    except ValueError:
        await update.message.reply_text(
            f'Invalid hours value "{hours_str}". Provide a number (e.g., 8.5).'
        )
        return

    if new_hours < 0:
        await update.message.reply_text("Hours cannot be negative.")
        return

    student = await db.find_student_by_name(name)
    if not student:
        await update.message.reply_text(
            f'No registered student matches "{name}".'
        )
        return

    log = await db.get_log_by_student_and_date(student["telegram_id"], date_str)
    if not log:
        await update.message.reply_text(
            f'No log entry found for {student["full_name"]} on {date_str}.'
        )
        return

    old_hours = log["hours"]
    await db.correct_hours(
        log["id"], old_hours, new_hours, update.effective_user.id,
    )

    old_display = old_hours if old_hours is not None else "none"
    await update.message.reply_text(
        f"Hours corrected for {student['full_name']} on {date_str}.\n"
        f"Old: {old_display} hrs -> New: {new_hours} hrs"
    )
