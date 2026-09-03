"""Desktop-only scheduling for local favorite refreshes."""

from apscheduler.schedulers.background import BackgroundScheduler

from src.config import REFRESH_MINUTES
from src.services.refresh import refresh_favorites


def create_refresh_scheduler() -> BackgroundScheduler:
    """Create a single-worker scheduler without starting it."""
    scheduler = BackgroundScheduler(
        daemon=True,
        job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": REFRESH_MINUTES * 60},
    )
    scheduler.add_job(
        refresh_favorites,
        trigger="interval",
        minutes=REFRESH_MINUTES,
        id="refresh-favorites",
        replace_existing=True,
    )
    return scheduler
