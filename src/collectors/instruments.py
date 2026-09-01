from src.database import get_instrument_name, instrument_catalog_is_fresh, save_instrument_catalog


def _columns(frame) -> tuple[str, str]:
    symbol_column = "Code" if "Code" in frame.columns else "Symbol"
    name_column = "Name"
    if symbol_column not in frame.columns or name_column not in frame.columns:
        raise ValueError("종목 목록에 코드 또는 기업명 컬럼이 없습니다")
    return symbol_column, name_column


def _read_listing(source: str) -> list[tuple[str, str]]:
    import FinanceDataReader as fdr

    frame = fdr.StockListing(source)
    symbol_column, name_column = _columns(frame)
    return [(str(row[symbol_column]).strip(), str(row[name_column]).strip()) for _, row in frame.iterrows()]


def resolve_company_name(symbol: str, market: str) -> str:
    normalized = symbol.upper().strip()
    cached_name = get_instrument_name(normalized, market)
    if cached_name:
        return cached_name
    if instrument_catalog_is_fresh(market):
        return normalized

    try:
        sources = ["KRX"] if market == "KR" else ["NASDAQ", "NYSE", "AMEX"]
        instruments = []
        for source in sources:
            instruments.extend(_read_listing(source))
        save_instrument_catalog(market, instruments)
        return next((name for code, name in instruments if code.upper() == normalized), normalized)
    except Exception:
        return normalized


def instrument_exists(symbol: str, market: str) -> bool | None:
    """Return True/False when the cached market catalog is available, else None."""
    normalized = symbol.upper().strip()
    if get_instrument_name(normalized, market):
        return True
    if instrument_catalog_is_fresh(market):
        return False
    try:
        sources = ["KRX"] if market == "KR" else ["NASDAQ", "NYSE", "AMEX"]
        instruments = []
        for source in sources:
            instruments.extend(_read_listing(source))
        save_instrument_catalog(market, instruments)
        return any(code.upper() == normalized for code, _ in instruments)
    except Exception:
        return None
