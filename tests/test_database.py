from datetime import datetime, timedelta, timezone

import pytest

from src import database
from src.models import MarketSnapshot, NewsArticle


@pytest.fixture(autouse=True)
def temporary_database(monkeypatch, tmp_path):
    database_path = tmp_path / "radar.db"
    database_path.touch()
    monkeypatch.setattr(database, "DB_PATH", database_path)


def test_favorites_are_normalized_sorted_and_removable():
    database.add_favorite("msft", "US")
    database.add_favorite("005930", "KR")

    assert database.list_favorites() == [("005930", "KR"), ("MSFT", "US")]

    database.remove_favorite("MSFT")
    assert database.list_favorites() == [("005930", "KR")]


def test_saved_market_snapshot_round_trips():
    captured_at = datetime(2026, 9, 2, 12, 30, tzinfo=timezone.utc)
    snapshot = MarketSnapshot("aapl", "Apple Inc.", 189.25, 1.24, 12_450_000, captured_at, "USD")

    database.save_market_snapshot("aapl", "US", snapshot)

    loaded = database.load_market_snapshot("AAPL", "US")
    assert loaded == MarketSnapshot("AAPL", "Apple Inc.", 189.25, 1.24, 12_450_000, captured_at, "USD")


def test_saved_articles_are_loaded_newest_first():
    now = datetime.now(timezone.utc)
    older = NewsArticle("Older", "Source", "https://example.com/older", now - timedelta(days=1), "old")
    newer = NewsArticle("Newer", "Source", "https://example.com/newer", now, "new")

    database.save_articles("aapl", [older, newer])

    assert [article.title for article in database.load_saved_articles("AAPL")] == ["Newer", "Older"]


def test_cleanup_old_articles_keeps_recent_and_undated_articles():
    now = datetime.now(timezone.utc)
    old = NewsArticle("Old", "Source", "https://example.com/old", now - timedelta(days=91))
    recent = NewsArticle("Recent", "Source", "https://example.com/recent", now - timedelta(days=1))
    undated = NewsArticle("Undated", "Source", "https://example.com/undated")
    database.save_articles("AAPL", [old, recent, undated])

    assert database.cleanup_old_articles(90) == 1
    assert [article.title for article in database.load_saved_articles("AAPL")] == ["Recent", "Undated"]


def test_collection_status_keeps_last_success_when_the_latest_attempt_fails():
    database.record_collection_status("news", "aapl", "US", "ok")
    successful_status = database.load_collection_status("news", "AAPL", "US")

    database.record_collection_status("news", "AAPL", "US", "unavailable", "network unavailable")
    failed_status = database.load_collection_status("news", "AAPL", "US")

    assert successful_status is not None
    assert failed_status is not None
    assert failed_status.status == "unavailable"
    assert failed_status.last_error == "network unavailable"
    assert failed_status.last_success_at == successful_status.last_success_at
    assert failed_status.last_attempt_at >= successful_status.last_attempt_at


def test_connections_use_wal_mode_and_a_busy_timeout():
    with database._connect() as connection:
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        busy_timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]

    assert journal_mode.lower() == "wal"
    assert busy_timeout == 5000


def test_article_flags_and_keywords_survive_refresh_upsert():
    article = NewsArticle("A title", "Source", "https://example.com/article", keywords=["market"])
    database.save_articles("AAPL", [article])
    database.set_article_flags(article.url, is_read=True, is_important=True)

    refreshed = NewsArticle("Updated title", "Source", article.url, keywords=["updated"])
    database.save_articles("AAPL", [refreshed])
    loaded = database.load_saved_articles("AAPL")[0]

    assert loaded.title == "Updated title"
    assert loaded.keywords == ["updated"]
    assert loaded.is_read is True
    assert loaded.is_important is True
