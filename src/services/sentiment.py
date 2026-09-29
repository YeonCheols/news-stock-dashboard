"""Dependency-free, title-focused sentiment classification for news articles."""

import re


POSITIVE_TERMS = {
    "beat", "beats", "better", "bullish", "gain", "gains", "growth", "improve", "improved",
    "increased", "profit", "profits", "rally", "record", "strong", "surge", "upgraded",
    "호재", "개선", "급등", "기대", "성장", "상승", "신고가", "증가", "흑자", "호실적",
}
NEGATIVE_TERMS = {
    "bearish", "crash", "cut", "cuts", "decline", "downgrade", "drop", "drops", "fall",
    "falls", "fraud", "loss", "losses", "risk", "weak", "warning",
    "악재", "감소", "급락", "하락", "적자", "우려", "위험", "경고", "부진", "손실", "리콜",
}

_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z'-]*|[가-힣]{2,}")


def classify_sentiment(title: str, summary: str = "") -> str:
    """Return ``positive``, ``negative``, or ``neutral`` from article text.

    This deliberately conservative first version uses an explainable word list.
    A tie or no matching term remains neutral rather than guessing.
    """
    tokens = {token.casefold() for token in _TOKEN_PATTERN.findall(f"{title} {summary}")}
    positive = len(tokens & POSITIVE_TERMS)
    negative = len(tokens & NEGATIVE_TERMS)
    if positive > negative:
        return "positive"
    if negative > positive:
        return "negative"
    return "neutral"
