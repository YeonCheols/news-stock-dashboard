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
