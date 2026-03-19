from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from bot import db
from bot.db import PHT
from bot.handlers.common import require_registration


def _fmt_time(iso: str) -> str:
    """Format an ISO timestamp to a human-readable 12-hour time string."""
    return datetime.fromisoformat(iso).strftime("%I:%M %p")


@require_registration
async def timein_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    log = await db.get_today_log(telegram_id)

    if log and log["time_in"]:
        await update.message.reply_text(
            f"You already timed in today at {_fmt_time(log['time_in'])}.\n"
            "Send /timeout when your shift ends."
        )
        return

    time_in_iso = await db.create_time_in(telegram_id)
    if time_in_iso is None:
        await update.message.reply_text(
            "Your time-in was already recorded. Send /timeout when your shift ends."
        )
        return

    await update.message.reply_text(
        f"Time-in recorded at {_fmt_time(time_in_iso)}.\n"
        "Send /timeout when your shift ends."
    )


@require_registration
async def timeout_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    log = await db.get_today_log(telegram_id)

    if not log or not log["time_in"]:
        await update.message.reply_text(
            "You haven't timed in today. Send /timein first."
        )
        return

    if log["time_out"]:
        await update.message.reply_text(
            f"You already timed out today at {_fmt_time(log['time_out'])}.\n"
            f"Today's hours: {log['hours']}"
        )
        return

    result = await db.update_time_out(log["id"], log["time_in"])
    if result is None:
        await update.message.reply_text(
            "Your time-out was already recorded. Send /status to check your hours."
        )
        return

    time_out_iso, hours = result
    total = await db.get_total_hours(telegram_id)
    await update.message.reply_text(
        f"Time-out recorded at {_fmt_time(time_out_iso)}.\n"
        f"Hours today: {hours}\n"
        f"Running total: {total}"
    )


@require_registration
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    student = context.user_data["student"]
    total = await db.get_total_hours(student["telegram_id"])
    required = student["required_hours"]
    remaining = round(required - total, 2)

    if remaining <= 0:
        await update.message.reply_text(
            f"Hours rendered: {total}\n"
            f"Hours required: {required}\n\n"
            "You have completed all required hours!"
        )
    else:
        await update.message.reply_text(
            f"Hours rendered: {total}\n"
            f"Hours required: {required}\n"
            f"Hours remaining: {remaining}"
        )
