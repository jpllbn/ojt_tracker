import logging
from datetime import time

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.config import (
    BOT_TOKEN,
    REMINDER_TIMEIN_HOUR,
    REMINDER_TIMEIN_MINUTE,
    REMINDER_TIMEOUT_HOUR,
    REMINDER_TIMEOUT_MINUTE,
)
from bot.db import init_db, PHT
from bot.handlers.start import registration_handler
from bot.handlers.hours import timein_command, timeout_command, status_command
from bot.handlers.coordinator import report_command, missing_command, hours_command
from bot.handlers.leave import leave_command
from bot.handlers.common import unknown_command
from bot.reminders import remind_timein, remind_timeout

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    await init_db()
    logger.info("Database initialised")


def main() -> None:
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(registration_handler)
    app.add_handler(CommandHandler("timein", timein_command))
    app.add_handler(CommandHandler("timeout", timeout_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("leave", leave_command))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CommandHandler("missing", missing_command))
    app.add_handler(CommandHandler("hours", hours_command))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    job_queue = app.job_queue
    job_queue.run_daily(
        remind_timein,
        time=time(REMINDER_TIMEIN_HOUR, REMINDER_TIMEIN_MINUTE, tzinfo=PHT),
        name="remind_timein",
    )
    job_queue.run_daily(
        remind_timeout,
        time=time(REMINDER_TIMEOUT_HOUR, REMINDER_TIMEOUT_MINUTE, tzinfo=PHT),
        name="remind_timeout",
    )

    logger.info("Starting OJT Tracker bot …")
    app.run_polling()


if __name__ == "__main__":
    main()
