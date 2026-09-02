import sys
from types import SimpleNamespace

from src.collectors import news


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return b"rss payload"


def test_news_cleans_deduplicates_and_sorts_entries(monkeypatch):
    entries = [
        {
            "link": "https://example.com/older",
            "title": "<b>Older</b> news",
            "summary": "<p>Older summary</p>",
            "published_parsed": (2026, 9, 1, 10, 0, 0, 0, 0, 0),
            "source": {"title": "Example News"},
        },
        {
            "link": "https://example.com/newer",
            "title": "Newer &amp; better",
            "summary": "<p>Newer summary</p>",
            "published_parsed": (2026, 9, 2, 10, 0, 0, 0, 0, 0),
        },
        {"link": "https://example.com/newer", "title": "Duplicate"},
    ]
    monkeypatch.setitem(sys.modules, "feedparser", SimpleNamespace(parse=lambda payload: SimpleNamespace(entries=entries)))
    monkeypatch.setattr(news, "urlopen", lambda request, timeout: FakeResponse())

    articles, error = news.get_news("AAPL", "US")

    assert error is None
    assert [article.title for article in articles] == ["Newer & better", "Older news"]
    assert articles[0].source == "Google News"
    assert articles[1].summary == "Older summary"


def test_news_returns_sample_when_rss_request_fails(monkeypatch):
    monkeypatch.setitem(sys.modules, "feedparser", SimpleNamespace())

    def fail_request(request, timeout):
        raise OSError("network unavailable")

    monkeypatch.setattr(news, "urlopen", fail_request)

    articles, error = news.get_news("AAPL", "US")

    assert len(articles) == 1
    assert articles[0].source == "샘플 뉴스"
    assert "network unavailable" in error
