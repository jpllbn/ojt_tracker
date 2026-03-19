import logging

from telegram.ext import Application, MessageHandler, filters

from bot.config import BOT_TOKEN
from bot.db import init_db
from bot.handlers.start import registration_handler
from bot.handlers.common import unknown_command

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
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    logger.info("Starting OJT Tracker bot …")
    app.run_polling()


if __name__ == "__main__":
    main()
