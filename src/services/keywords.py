"""Small dependency-free keyword extraction for RSS articles."""

from collections import Counter
import re


_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9&.-]{2,}|[가-힣]{2,}")
_STOPWORDS = {
    "about", "after", "also", "from", "have", "into", "more", "news", "that", "this", "with",
    "관련", "대한", "따른", "대한", "에서", "으로", "있는", "있다", "하는", "했다", "및", "주식", "시장",
}


def extract_keywords(title: str, summary: str = "", limit: int = 5) -> list[str]:
    """Return frequent, useful-looking terms from an article title and summary."""
    tokens = [token.lower() for token in _TOKEN_PATTERN.findall(f"{title} {summary}")]
    counts = Counter(token for token in tokens if token not in _STOPWORDS)
    return [token for token, _ in counts.most_common(limit)]
