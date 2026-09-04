from src.services.keywords import extract_keywords


def test_extract_keywords_supports_korean_and_english_and_filters_common_words():
    keywords = extract_keywords("반도체 실적 전망", "반도체 기업의 실적 전망과 AI 투자 뉴스")

    assert keywords[:3] == ["반도체", "실적", "전망"]
    assert "뉴스" not in keywords


def test_extract_keywords_limits_results():
    assert len(extract_keywords("alpha beta gamma delta epsilon zeta", limit=3)) == 3
