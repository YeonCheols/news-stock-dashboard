"""Refresh and persist market data without coupling collection to the UI."""

import logging

from src.collectors.market import get_market_snapshot
from src.collectors.news import get_news
from src.config import DATA_RETENTION_DAYS
from src.database import (
    cleanup_old_articles,
    list_favorites,
    record_collection_status,
    save_articles,
    save_market_snapshot,
)
from src.models import MarketSnapshot, NewsArticle


logger = logging.getLogger(__name__)


def refresh_symbol(symbol: str, market: str) -> tuple[MarketSnapshot, list[NewsArticle], str | None, str, str | None]:
    """Collect one symbol and persist every successful source independently."""
    snapshot, market_error, market_status = get_market_snapshot(symbol, market)
    record_collection_status("market", snapshot.symbol, market, market_status, market_error)
    if market_status == "invalid":
        return snapshot, [], market_error, market_status, "유효하지 않은 종목 코드입니다"
    if not market_error:
        save_market_snapshot(snapshot.symbol, market, snapshot)

    articles, news_error = get_news(snapshot.symbol, market)
    record_collection_status("news", snapshot.symbol, market, "ok" if not news_error else "unavailable", news_error)
    if not news_error:
        save_articles(snapshot.symbol, articles)
        cleanup_old_articles(DATA_RETENTION_DAYS)
    return snapshot, articles, market_error, market_status, news_error


def refresh_favorites() -> None:
    """Refresh favorites sequentially so one broken symbol cannot stop the batch."""
    for symbol, market in list_favorites():
        try:
            refresh_symbol(symbol, market)
        except Exception as exc:
            logger.exception("Unexpected refresh failure for %s (%s)", symbol, market)
            try:
                record_collection_status("market", symbol, market, "unavailable", str(exc))
            except Exception:
                logger.exception("Could not persist refresh failure for %s (%s)", symbol, market)
