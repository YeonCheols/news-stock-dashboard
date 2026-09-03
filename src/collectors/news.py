from datetime import datetime, timezone
from html import unescape
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.models import NewsArticle
from src.collectors.retry import run_with_retries
from src.config import DATA_REQUEST_TIMEOUT_SECONDS


def _sample(symbol: str) -> list[NewsArticle]:
    return [NewsArticle(f"{symbol} 관련 최신 시장 동향", "샘플 뉴스", "https://news.google.com/", datetime.now(timezone.utc), "실제 RSS 연결 전 화면 확인을 위한 샘플 뉴스입니다.", [symbol, "시장", "투자"])]


def _clean(value: str) -> str:
    return re.sub(r"<[^>]+>", "", unescape(value or "")).strip()


def get_news(symbol: str, market: str) -> tuple[list[NewsArticle], str | None]:
    try:
        import feedparser

        query = f"{symbol} stock" if market == "US" else f"{symbol} 주식"
        rss_url = "https://news.google.com/rss/search?" + urlencode({"q": query, "hl": "ko", "gl": "KR", "ceid": "KR:ko"})
        request = Request(rss_url, headers={"User-Agent": "Mozilla/5.0 news-stock-dashboard/0.1"})
        def fetch_rss() -> bytes:
            with urlopen(request, timeout=DATA_REQUEST_TIMEOUT_SECONDS) as response:
                return response.read()

        feed = feedparser.parse(run_with_retries(fetch_rss))
        if not feed.entries:
            raise ValueError("RSS 응답에 뉴스가 없습니다")
        articles, seen = [], set()
        for entry in feed.entries:
            url, title = entry.get("link", ""), _clean(entry.get("title", ""))
            if not url or not title or url in seen:
                continue
            seen.add(url)
            published = None
            if published_parsed := entry.get("published_parsed"):
                published = datetime(*published_parsed[:6], tzinfo=timezone.utc)
            source = entry.get("source", {}).get("title", "Google News")
            articles.append(NewsArticle(title, source, url, published, _clean(entry.get("summary", "")), [symbol]))
        oldest = datetime.min.replace(tzinfo=timezone.utc)
        articles.sort(key=lambda article: article.published_at or oldest, reverse=True)
        return articles[:10], None if articles else "RSS 응답에 뉴스가 없습니다"
    except Exception as exc:
        return _sample(symbol), str(exc)
