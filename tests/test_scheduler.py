from src.services.scheduler import create_refresh_scheduler


def test_refresh_scheduler_has_one_non_overlapping_interval_job():
    scheduler = create_refresh_scheduler()
    scheduler.start()
    job = scheduler.get_job("refresh-favorites")

    assert job is not None
    assert job.coalesce is True
    assert job.max_instances == 1
    assert job.trigger.interval.total_seconds() > 0
    assert scheduler.running is True
    scheduler.shutdown(wait=False)
    assert scheduler.running is False
