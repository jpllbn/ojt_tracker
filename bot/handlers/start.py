from telegram import Update
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot import db
from bot.config import REQUIRED_HOURS

AWAITING_NAME, AWAITING_SECTION = range(2)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    student = await db.get_student(update.effective_user.id)
    if student:
        await update.message.reply_text(
            f"You're already registered as {student['full_name']} "
            f"({student['section']}).\n"
            "Use /status to check your hours."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Welcome to OJT Tracker!\n\n"
        "Let's get you registered. Please send your full name."
    )
    return AWAITING_NAME


async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text(
            "Name cannot be empty. Please send your full name."
        )
        return AWAITING_NAME

    context.user_data["reg_name"] = name
    await update.message.reply_text(
        f"Got it, {name}.\n\nNow send your section (e.g. BSIT-3A)."
    )
    return AWAITING_SECTION


async def received_section(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    section = update.message.text.strip()
    if not section:
        await update.message.reply_text(
            "Section cannot be empty. Please send your section (e.g. BSIT-3A)."
        )
        return AWAITING_SECTION

    full_name = context.user_data.pop("reg_name")

    await db.create_student(
        telegram_id=update.effective_user.id,
        full_name=full_name,
        section=section,
        required_hours=REQUIRED_HOURS,
    )

    await update.message.reply_text(
        "Registration complete!\n\n"
        f"Name: {full_name}\n"
        f"Section: {section}\n"
        f"Required hours: {REQUIRED_HOURS}\n\n"
        "You can now use /timein and /timeout to log your hours."
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("reg_name", None)
    await update.message.reply_text("Registration cancelled.")
    return ConversationHandler.END


async def _command_during_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await update.message.reply_text(
        "Please complete your registration first, or send /cancel to abort."
    )


registration_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_command)],
    states={
        AWAITING_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, received_name),
        ],
        AWAITING_SECTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, received_section),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        MessageHandler(filters.COMMAND, _command_during_registration),
    ],
)
