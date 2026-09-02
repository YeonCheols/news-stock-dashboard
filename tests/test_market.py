import sys
from types import SimpleNamespace

from src.collectors import market


def test_market_snapshot_returns_sample_when_provider_fails(monkeypatch):
    class BrokenTicker:
        def __init__(self, symbol):
            raise RuntimeError("provider unavailable")

    monkeypatch.setitem(sys.modules, "yfinance", SimpleNamespace(Ticker=BrokenTicker))

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
