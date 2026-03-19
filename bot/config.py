import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
COORDINATOR_CHAT_ID: int = int(os.environ["COORDINATOR_CHAT_ID"])
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "ojt_tracker.db")
REQUIRED_HOURS: float = float(os.getenv("REQUIRED_HOURS", "500"))

REMINDER_TIMEIN_HOUR: int = int(os.getenv("REMINDER_TIMEIN_HOUR", "8"))
REMINDER_TIMEIN_MINUTE: int = int(os.getenv("REMINDER_TIMEIN_MINUTE", "0"))
REMINDER_TIMEOUT_HOUR: int = int(os.getenv("REMINDER_TIMEOUT_HOUR", "17"))
REMINDER_TIMEOUT_MINUTE: int = int(os.getenv("REMINDER_TIMEOUT_MINUTE", "30"))
