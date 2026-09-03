import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MARKET = os.getenv("DEFAULT_MARKET", "US").upper()
REFRESH_MINUTES = max(1, int(os.getenv("NEWS_REFRESH_MINUTES", "30")))
MANUAL_REFRESH_COOLDOWN_SECONDS = max(30, int(os.getenv("MANUAL_REFRESH_COOLDOWN_SECONDS", "60")))
DATA_REQUEST_TIMEOUT_SECONDS = max(1, int(os.getenv("DATA_REQUEST_TIMEOUT_SECONDS", "10")))
DATA_REQUEST_MAX_RETRIES = max(0, int(os.getenv("DATA_REQUEST_MAX_RETRIES", "2")))
DATA_REQUEST_RETRY_DELAY_SECONDS = max(0, float(os.getenv("DATA_REQUEST_RETRY_DELAY_SECONDS", "1")))
DATA_RETENTION_DAYS = max(1, int(os.getenv("DATA_RETENTION_DAYS", "90")))
SCHEDULED_COLLECTION_ENABLED = os.getenv("SCHEDULED_COLLECTION_ENABLED", "true").lower() not in {"0", "false", "no"}
