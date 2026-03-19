import functools

from telegram import Update
from telegram.ext import ContextTypes

from bot import db


def require_registration(func):
    """Decorator: blocks the command and redirects to /start if unregistered."""

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        student = await db.get_student(update.effective_user.id)
        if not student:
            await update.message.reply_text(
                "You're not registered yet. Send /start to set up your account."
            )
            return
        context.user_data["student"] = student
        return await func(update, context, *args, **kwargs)

    return wrapper


def coordinator_only(func):
    """Decorator: restricts a handler to the configured coordinator chat ID."""

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        from bot.config import COORDINATOR_CHAT_ID

        if update.effective_user.id != COORDINATOR_CHAT_ID:
            await update.message.reply_text("You are not authorized to use this command.")
            return
        return await func(update, context, *args, **kwargs)

    return wrapper


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from bot.config import COORDINATOR_CHAT_ID

    text = (
        "I don't recognize that command.\n\n"
        "Available commands:\n"
        "/start   \u2014 Register your account\n"
        "/timein  \u2014 Log your time in\n"
        "/timeout \u2014 Log your time out\n"
        "/status  \u2014 Check your hours\n"
        "/cancel  \u2014 Cancel current operation"
    )

    if update.effective_user.id == COORDINATOR_CHAT_ID:
        text += (
            "\n\nCoordinator commands:\n"
            "/report          \u2014 Who logged today\n"
            "/missing         \u2014 Who hasn't logged today\n"
            "/hours <name>    \u2014 Student's full log"
        )

    await update.message.reply_text(text)
