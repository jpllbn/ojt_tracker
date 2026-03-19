import logging

from telegram.ext import ContextTypes

from bot import db

logger = logging.getLogger(__name__)


async def remind_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a reminder to students who timed in but haven't timed out today."""
    open_ids = await db.get_open_sessions_today()
    if not open_ids:
        logger.info("Timeout reminder: no open sessions")
        return

    failed = 0
    for tid in open_ids:
        try:
            await context.bot.send_message(
                chat_id=tid,
                text=(
                    "Reminder: you timed in today but haven't timed out yet.\n"
                    "Send /timeout before you leave."
                ),
            )
        except Exception:
            failed += 1
            logger.warning("Failed to send timeout reminder to %s", tid)

    sent = len(open_ids) - failed
    logger.info("Timeout reminder: %d sent, %d failed out of %d", sent, failed, len(open_ids))


async def remind_timein(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a morning reminder to students who haven't timed in today."""
    missing_ids = await db.get_students_without_timein_today()
    if not missing_ids:
        logger.info("Timein reminder: all students already timed in")
        return

    failed = 0
    for tid in missing_ids:
        try:
            await context.bot.send_message(
                chat_id=tid,
                text=(
                    "Good morning! Don't forget to log your time-in.\n"
                    "Send /timein when your shift starts."
                ),
            )
        except Exception:
            failed += 1
            logger.warning("Failed to send timein reminder to %s", tid)

    sent = len(missing_ids) - failed
    logger.info("Timein reminder: %d sent, %d failed out of %d", sent, failed, len(missing_ids))
