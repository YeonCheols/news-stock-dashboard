import sys
from types import SimpleNamespace

from src.collectors import market
from src.collectors import retry


def test_market_snapshot_returns_sample_when_provider_fails(monkeypatch):
    class BrokenTicker:
        def __init__(self, symbol):
            raise RuntimeError("provider unavailable")

    monkeypatch.setitem(sys.modules, "yfinance", SimpleNamespace(Ticker=BrokenTicker))
    monkeypatch.setattr(retry, "DATA_REQUEST_MAX_RETRIES", 0)

    snapshot, error, status = market.get_market_snapshot(" aapl ", "US")

    assert snapshot.symbol == "AAPL"
    assert snapshot.price == 189.25
    assert status == "unavailable"
    assert "provider unavailable" in error


def test_market_snapshot_marks_known_invalid_symbol(monkeypatch):
    class EmptyHistory:
        empty = True

    class EmptyTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, **kwargs):
            return EmptyHistory()

    monkeypatch.setitem(sys.modules, "yfinance", SimpleNamespace(Ticker=EmptyTicker))
    monkeypatch.setattr(market, "instrument_exists", lambda symbol, market_name: False)

    snapshot, error, status = market.get_market_snapshot("bad", "US")

    assert snapshot.symbol == "BAD"
    assert error == "유효하지 않은 종목 코드입니다"
    assert status == "invalid"


def test_market_snapshot_retries_history_request(monkeypatch):
    calls = []

    class History:
        empty = True

    class RetryingTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise TimeoutError("timeout")
            return History()

    monkeypatch.setitem(sys.modules, "yfinance", SimpleNamespace(Ticker=RetryingTicker))
    monkeypatch.setattr(market, "instrument_exists", lambda symbol, market_name: False)
    monkeypatch.setattr(retry, "DATA_REQUEST_MAX_RETRIES", 1)
    monkeypatch.setattr(retry.time, "sleep", lambda delay: None)

    _, _, status = market.get_market_snapshot("BAD", "US")

    assert status == "invalid"
    assert len(calls) == 2
    assert calls[0]["timeout"] == market.DATA_REQUEST_TIMEOUT_SECONDS
