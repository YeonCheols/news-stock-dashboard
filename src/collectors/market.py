from datetime import datetime, timezone

from src.models import MarketSnapshot
from src.collectors.instruments import resolve_company_name
from src.collectors.instruments import instrument_exists


def _sample(symbol: str, market: str) -> MarketSnapshot:
    name = symbol
    price = 72_400 if market == "KR" else 189.25
    currency = "KRW" if market == "KR" else "USD"
    return MarketSnapshot(symbol, name, price, 1.24, 12_450_000, datetime.now(timezone.utc), currency)


def get_market_snapshot(symbol: str, market: str) -> tuple[MarketSnapshot, str | None, str]:
    normalized = symbol.upper().strip()
    try:
        import yfinance as yf

        ticker = yf.Ticker(f"{normalized}.KS" if market == "KR" and normalized.isdigit() else normalized)
        history = ticker.history(period="5d", auto_adjust=False)
        if history.empty:
            if instrument_exists(normalized, market) is False:
                return _sample(normalized, market), "유효하지 않은 종목 코드입니다", "invalid"
            raise ValueError("가격 데이터가 없습니다")
        latest = history.iloc[-1]
        previous = history.iloc[-2] if len(history) > 1 else latest
        price = float(latest["Close"])
        change_rate = (price - float(previous["Close"])) / float(previous["Close"]) * 100
        volume = int(latest.get("Volume", 0))
        name = resolve_company_name(normalized, market)
        currency = "KRW" if market == "KR" else "USD"
        observed_at = latest.name.to_pydatetime() if hasattr(latest.name, "to_pydatetime") else datetime.now(timezone.utc)
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        return MarketSnapshot(normalized, name, price, change_rate, volume, observed_at, currency), None, "ok"
    except Exception as exc:
        return _sample(normalized, market), str(exc), "unavailable"


def get_price_history(symbol: str, market: str):
    """Return a daily close series for the optional dashboard chart."""
    import yfinance as yf

    ticker = yf.Ticker(f"{symbol}.KS" if market == "KR" and symbol.isdigit() else symbol)
    history = ticker.history(period="1mo", auto_adjust=False)
    if history.empty or "Close" not in history:
        raise ValueError("차트용 가격 데이터가 없습니다")
    close = history["Close"]
    if hasattr(close, "columns"):
        close = close.iloc[:, 0]
    return close.rename("종가")
