import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
COORDINATOR_CHAT_ID: int = int(os.environ["COORDINATOR_CHAT_ID"])
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "ojt_tracker.db")
REQUIRED_HOURS: float = float(os.getenv("REQUIRED_HOURS", "500"))
