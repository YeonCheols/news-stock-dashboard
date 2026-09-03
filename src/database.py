import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
import shutil

from src.models import CollectionStatus, MarketSnapshot, NewsArticle



def _data_directory() -> Path:
    """Return a writable per-user data directory, with a dev override."""
    if os.getenv("RADAR_DATA_DIR"):
        return Path(os.environ["RADAR_DATA_DIR"]).expanduser()
    if os.name == "nt":
        return Path(os.getenv("APPDATA", Path.home())) / "NewsStockDashboard"
    if os.name == "posix" and os.getenv("XDG_DATA_HOME"):
        return Path(os.environ["XDG_DATA_HOME"]) / "news-stock-dashboard"
    if os.name == "posix" and Path.home().joinpath("Library").exists():
        return Path.home() / "Library" / "Application Support" / "NewsStockDashboard"
    return Path.home() / ".local" / "share" / "news-stock-dashboard"


DB_PATH = _data_directory() / "radar.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    legacy_path = Path(__file__).resolve().parents[1] / "data" / "radar.db"
    if not DB_PATH.exists() and legacy_path.exists() and legacy_path != DB_PATH:
        shutil.copy2(legacy_path, DB_PATH)
    connection = sqlite3.connect(DB_PATH, timeout=5)
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("CREATE TABLE IF NOT EXISTS favorites (symbol TEXT PRIMARY KEY, market TEXT NOT NULL)")
    connection.execute(
        "CREATE TABLE IF NOT EXISTS articles (url TEXT PRIMARY KEY, title TEXT NOT NULL, source TEXT, "
        "published_at TEXT, summary TEXT, symbol TEXT NOT NULL)"
    )
    connection.execute(
        "CREATE TABLE IF NOT EXISTS market_snapshots (symbol TEXT PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, "
        "change_rate REAL NOT NULL, volume INTEGER NOT NULL, captured_at TEXT NOT NULL, market TEXT NOT NULL)"
    )
    connection.execute(
        "CREATE TABLE IF NOT EXISTS instruments (symbol TEXT NOT NULL, market TEXT NOT NULL, name TEXT NOT NULL, "
        "updated_at TEXT NOT NULL, PRIMARY KEY(symbol, market))"
    )
    connection.execute(
        "CREATE TABLE IF NOT EXISTS collection_statuses (source TEXT NOT NULL, symbol TEXT NOT NULL, market TEXT NOT NULL, "
        "status TEXT NOT NULL, last_attempt_at TEXT NOT NULL, last_success_at TEXT, last_error TEXT, "
        "PRIMARY KEY(source, symbol, market))"
    )
    connection.commit()
    return connection


def list_favorites() -> list[tuple[str, str]]:
    with _connect() as connection:
        return connection.execute("SELECT symbol, market FROM favorites ORDER BY symbol").fetchall()


def add_favorite(symbol: str, market: str) -> None:
    with _connect() as connection:
        connection.execute("INSERT OR REPLACE INTO favorites(symbol, market) VALUES (?, ?)", (symbol.upper(), market))
        connection.commit()


def remove_favorite(symbol: str) -> None:
    with _connect() as connection:
        connection.execute("DELETE FROM favorites WHERE symbol = ?", (symbol.upper(),))
        connection.commit()


def save_articles(symbol: str, articles: list[NewsArticle]) -> None:
    with _connect() as connection:
        connection.executemany(
            "INSERT OR REPLACE INTO articles(url, title, source, published_at, summary, symbol) VALUES (?, ?, ?, ?, ?, ?)",
            [(a.url, a.title, a.source, a.published_at.isoformat() if a.published_at else None, a.summary, symbol.upper()) for a in articles],
        )
        connection.commit()


def cleanup_old_articles(retention_days: int) -> int:
    """Remove dated articles older than the retention period and keep undated entries."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    with _connect() as connection:
        cursor = connection.execute("DELETE FROM articles WHERE published_at IS NOT NULL AND published_at < ?", (cutoff,))
        connection.commit()
        return cursor.rowcount


def save_market_snapshot(symbol: str, market: str, snapshot: MarketSnapshot) -> None:
    with _connect() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO market_snapshots(symbol, name, price, change_rate, volume, captured_at, market) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (symbol.upper(), snapshot.name, snapshot.price, snapshot.change_rate, snapshot.volume, snapshot.captured_at.isoformat(), market),
        )
        connection.commit()


def load_market_snapshot(symbol: str, market: str) -> MarketSnapshot | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT symbol, name, price, change_rate, volume, captured_at FROM market_snapshots WHERE symbol = ? AND market = ?",
            (symbol.upper(), market),
        ).fetchone()
    if not row:
        return None
    currency = "KRW" if market == "KR" else "USD"
    return MarketSnapshot(row[0], row[1], row[2], row[3], row[4], datetime.fromisoformat(row[5]), currency)


def load_saved_articles(symbol: str) -> list[NewsArticle]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT title, source, url, published_at, summary FROM articles WHERE symbol = ? "
            "ORDER BY published_at DESC LIMIT 10",
            (symbol.upper(),),
        ).fetchall()
    return [NewsArticle(title, source or "알 수 없음", url, datetime.fromisoformat(published) if published else None, summary or "", [symbol]) for title, source, url, published, summary in rows]


def record_collection_status(source: str, symbol: str, market: str, status: str, error: str | None = None) -> None:
    """Record the last collection attempt without losing the last successful time."""
    attempted_at = datetime.now(timezone.utc).isoformat()
    successful_at = attempted_at if status == "ok" else None
    with _connect() as connection:
        connection.execute(
            "INSERT INTO collection_statuses(source, symbol, market, status, last_attempt_at, last_success_at, last_error) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(source, symbol, market) DO UPDATE SET "
            "status = excluded.status, last_attempt_at = excluded.last_attempt_at, "
            "last_success_at = COALESCE(excluded.last_success_at, collection_statuses.last_success_at), "
            "last_error = excluded.last_error",
            (source, symbol.upper(), market, status, attempted_at, successful_at, error),
        )
        connection.commit()


def load_collection_status(source: str, symbol: str, market: str) -> CollectionStatus | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT source, symbol, market, status, last_attempt_at, last_success_at, last_error "
            "FROM collection_statuses WHERE source = ? AND symbol = ? AND market = ?",
            (source, symbol.upper(), market),
        ).fetchone()
    if not row:
        return None
    return CollectionStatus(
        row[0], row[1], row[2], row[3], datetime.fromisoformat(row[4]),
        datetime.fromisoformat(row[5]) if row[5] else None, row[6],
    )


def get_instrument_name(symbol: str, market: str) -> str | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT name FROM instruments WHERE symbol = ? AND market = ?", (symbol.upper(), market)
        ).fetchone()
    return row[0] if row else None


def instrument_catalog_is_fresh(market: str, max_age_hours: int = 24) -> bool:
    with _connect() as connection:
        row = connection.execute(
            "SELECT MAX(updated_at) FROM instruments WHERE market = ?", (market,)
        ).fetchone()
    if not row or not row[0]:
        return False
    return (datetime.now().astimezone() - datetime.fromisoformat(row[0]).astimezone()).total_seconds() < max_age_hours * 3600


def save_instrument_catalog(market: str, instruments: list[tuple[str, str]]) -> None:
    updated_at = datetime.now().astimezone().isoformat()
    with _connect() as connection:
        connection.executemany(
            "INSERT OR REPLACE INTO instruments(symbol, market, name, updated_at) VALUES (?, ?, ?, ?)",
            [(symbol.upper(), market, name, updated_at) for symbol, name in instruments if symbol and name],
        )
        connection.commit()
