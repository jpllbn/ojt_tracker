from telegram import Update
from telegram.ext import ContextTypes

from bot import db
from bot.handlers.common import require_registration


@require_registration
async def leave_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "Please provide a reason for your leave.\n"
            "Example: /leave Sick day"
        )
        return

    existing_log = await db.get_today_log(telegram_id)
    if existing_log and existing_log["time_in"]:
        await update.message.reply_text(
            "You already have a time-in entry for today.\n"
            "Use /timeout to end your shift instead."
        )
        return

    existing_leave = await db.get_today_leave(telegram_id)
    if existing_leave:
        await update.message.reply_text(
            f"You already filed a leave for today.\n"
            f"Reason: {existing_leave['reason']}"
        )
        return

    reason = " ".join(context.args)
    result = await db.create_leave(telegram_id, reason)

    if result == "has_timelog":
        await update.message.reply_text(
            "You already have a time-in entry for today.\n"
            "Use /timeout to end your shift instead."
        )
        return

    if result == "duplicate":
        await update.message.reply_text(
            "Your leave was already recorded for today."
        )
        return

    await update.message.reply_text(
        f"Leave recorded for today.\nReason: {reason}"
    )
