from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MarketSnapshot:
    symbol: str
    name: str
    price: float
    change_rate: float
    volume: int = 0
    captured_at: datetime | None = None
    currency: str = "USD"

    @property
    def price_display(self) -> str:
        if self.currency == "KRW":
            return f"{self.price:,.0f}원"
        return f"${self.price:,.2f}"

    @property
    def change_display(self) -> str:
        return f"{self.change_rate:+.2f}%"


@dataclass
class NewsArticle:
    title: str
    source: str
    url: str
    published_at: datetime | None = None
    summary: str = ""
    keywords: list[str] = field(default_factory=list)


@dataclass
class CollectionStatus:
    source: str
    symbol: str
    market: str
    status: str
    last_attempt_at: datetime
    last_success_at: datetime | None = None
    last_error: str | None = None
