import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MARKET = os.getenv("DEFAULT_MARKET", "US").upper()
REFRESH_MINUTES = max(1, int(os.getenv("NEWS_REFRESH_MINUTES", "30")))
MANUAL_REFRESH_COOLDOWN_SECONDS = max(30, int(os.getenv("MANUAL_REFRESH_COOLDOWN_SECONDS", "60")))
