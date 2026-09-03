from datetime import datetime, timezone

from src.models import MarketSnapshot, NewsArticle
from src.services import refresh


def test_refresh_symbol_persists_each_successful_source(monkeypatch):
    snapshot = MarketSnapshot("AAPL", "Apple Inc.", 189.25, 1.24, 100, datetime.now(timezone.utc), "USD")
    articles = [NewsArticle("News", "Source", "https://example.com/news")]
    statuses = []
    saved = []
    monkeypatch.setattr(refresh, "get_market_snapshot", lambda symbol, market: (snapshot, None, "ok"))
    monkeypatch.setattr(refresh, "get_news", lambda symbol, market: (articles, None))
    monkeypatch.setattr(refresh, "record_collection_status", lambda *args: statuses.append(args))
    monkeypatch.setattr(refresh, "save_market_snapshot", lambda *args: saved.append(("market", args)))
    monkeypatch.setattr(refresh, "save_articles", lambda *args: saved.append(("news", args)))
    monkeypatch.setattr(refresh, "cleanup_old_articles", lambda days: saved.append(("cleanup", days)))

    result = refresh.refresh_symbol("aapl", "US")

    assert result == (snapshot, articles, None, "ok", None)
    assert statuses == [("market", "AAPL", "US", "ok", None), ("news", "AAPL", "US", "ok", None)]
    assert [entry[0] for entry in saved] == ["market", "news", "cleanup"]


def test_refresh_favorites_continues_after_an_unexpected_symbol_failure(monkeypatch):
    refreshed = []
    failures = []
    monkeypatch.setattr(refresh, "list_favorites", lambda: [("FAIL", "US"), ("AAPL", "US")])

    def refresh_one(symbol, market):
        refreshed.append((symbol, market))
        if symbol == "FAIL":
            raise RuntimeError("unexpected failure")

    monkeypatch.setattr(refresh, "refresh_symbol", refresh_one)
    monkeypatch.setattr(refresh, "record_collection_status", lambda *args: failures.append(args))

    refresh.refresh_favorites()

    assert refreshed == [("FAIL", "US"), ("AAPL", "US")]
    assert failures == [("market", "FAIL", "US", "unavailable", "unexpected failure")]
