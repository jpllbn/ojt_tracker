from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from bot import db
from bot.handlers.common import coordinator_only


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
    total = await db.get_total_hours(student["telegram_id"])

    header = (
        f"{student['full_name']} ({student['section']})\n"
        f"Required: {student['required_hours']} hrs | "
        f"Rendered: {total} hrs\n"
    )

    if not logs:
        await update.message.reply_text(header + "\nNo sessions recorded yet.")
        return

    lines = [header, "Date       | In       | Out      | Hours"]
    for log in logs:
        hrs = log["hours"] if log["hours"] is not None else "—"
        lines.append(
            f"{log['date']} | {_fmt_time(log['time_in'])} | "
            f"{_fmt_time(log['time_out'])} | {hrs}"
        )

    await update.message.reply_text("\n".join(lines))
