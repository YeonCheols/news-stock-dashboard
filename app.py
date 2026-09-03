"""News & stock radar Streamlit application."""

from datetime import date, datetime, timedelta, timezone

import streamlit as st

from src.collectors.market import get_price_history
from src.config import DEFAULT_MARKET, MANUAL_REFRESH_COOLDOWN_SECONDS, REFRESH_MINUTES
from src.database import (
    add_favorite,
    list_favorites,
    load_collection_status,
    load_market_snapshot,
    load_saved_articles,
    remove_favorite,
)
from src.services.refresh import refresh_symbol

st.set_page_config(page_title="뉴스·주식 레이더", page_icon="📡", layout="wide")


def format_time(value: datetime | None) -> str:
    return value.astimezone().strftime("%Y-%m-%d %H:%M") if value else "시각 없음"


@st.cache_data(ttl=REFRESH_MINUTES * 60, show_spinner=False)
def load_data(symbol: str, market: str):
    return refresh_symbol(symbol, market)


@st.cache_data(ttl=REFRESH_MINUTES * 60, show_spinner=False)
def load_price_history(symbol: str, market: str):
    return get_price_history(symbol, market)


st.title("📡 뉴스·주식 레이더")
st.caption("관심 종목의 현재가와 최근 뉴스를 한 화면에서 확인하세요.")

with st.sidebar:
    st.header("종목 조회")
    favorites = list_favorites()
    favorite_labels = [f"{favorite_symbol} ({favorite_market})" for favorite_symbol, favorite_market in favorites]
    selected_favorite = st.selectbox("관심 종목", ["직접 입력"] + favorite_labels)
    favorite_selected = selected_favorite != "직접 입력"
    selected_symbol = selected_favorite.split(" (")[0] if favorite_selected else "AAPL"
    selected_market = next((m for s, m in favorites if s == selected_symbol), DEFAULT_MARKET)
    typed_symbol = st.text_input(
        "종목명 또는 티커",
        value=selected_symbol,
        placeholder="예: AAPL, 005930",
        disabled=favorite_selected,
        help="관심 종목을 선택한 경우 선택된 종목이 조회 대상입니다. 다른 종목은 '직접 입력'을 선택하세요.",
    )
    typed_market = st.selectbox(
        "시장",
        ["US", "KR"],
        index=0 if selected_market == "US" else 1,
        disabled=favorite_selected,
    )
    add_col, remove_col = st.columns(2)
    symbol = selected_symbol if favorite_selected else typed_symbol
    market = selected_market if favorite_selected else typed_market
    normalized_symbol = symbol.strip().upper()
    if add_col.button("관심 추가", use_container_width=True, disabled=not normalized_symbol):
        add_favorite(normalized_symbol, market)
        st.session_state["favorite_message"] = f"{normalized_symbol} ({market}) 종목을 관심 목록에 추가했습니다."
        st.rerun()
    if remove_col.button("관심 삭제", use_container_width=True, disabled=not normalized_symbol):
        remove_favorite(normalized_symbol)
        st.session_state["favorite_message"] = f"{normalized_symbol} 종목을 관심 목록에서 삭제했습니다."
        st.rerun()
    if st.button("데이터 새로고침", use_container_width=True):
        refresh_key = f"{normalized_symbol}:{market}"
        now = datetime.now(timezone.utc).timestamp()
        last_refresh = st.session_state.get("last_manual_refresh", {}).get(refresh_key, 0)
        if now - last_refresh < MANUAL_REFRESH_COOLDOWN_SECONDS:
            wait_seconds = int(MANUAL_REFRESH_COOLDOWN_SECONDS - (now - last_refresh))
            st.session_state["refresh_message"] = f"요청 보호를 위해 {wait_seconds}초 후 다시 시도해 주세요."
        else:
            refreshes = st.session_state.setdefault("last_manual_refresh", {})
            refreshes[refresh_key] = now
            load_data.clear()
        st.rerun()
    st.divider()
    st.caption(f"자동 캐시 주기: {REFRESH_MINUTES}분")
    st.caption(f"데스크톱 실행 시 관심 종목 자동 수집: {REFRESH_MINUTES}분")
    st.caption("※ 데이터는 참고용이며 투자 추천이 아닙니다.")
    if message := st.session_state.pop("favorite_message", None):
        st.success(message)
    if message := st.session_state.pop("refresh_message", None):
        st.warning(message)
    st.divider()
    st.subheader("뉴스 필터")
    date_range = st.date_input(
        "발행 기간",
        value=(date.today() - timedelta(days=30), date.today()),
        max_value=date.today(),
    )
    keyword_query = st.text_input("키워드 검색", placeholder="예: 실적, 반도체")
    show_chart = st.checkbox("최근 1개월 주가 차트", value=False)

if not symbol.strip():
    st.info("왼쪽에서 종목명 또는 티커를 입력해 주세요.")
    st.stop()

with st.spinner("시장 데이터와 뉴스를 불러오는 중…"):
    snapshot, articles, market_error, market_status, news_error = load_data(symbol.strip(), market)
using_saved_snapshot = False
using_saved_articles = False
if market_status == "invalid":
    st.error(f"{symbol.strip().upper()}은(는) 유효하지 않은 종목 코드입니다. 시장 선택과 티커를 확인해 주세요.")
    st.stop()
saved_snapshot = load_market_snapshot(snapshot.symbol, market)
if saved_snapshot:
    snapshot = saved_snapshot
    using_saved_snapshot = bool(market_error)
saved_articles = load_saved_articles(snapshot.symbol)
if saved_articles:
    articles = saved_articles
    using_saved_articles = bool(news_error)
if using_saved_snapshot:
    st.info("주가 API가 응답하지 않아 마지막 성공 데이터를 표시합니다.")
if using_saved_articles:
    st.info("뉴스 RSS가 응답하지 않아 마지막 성공 뉴스를 표시합니다.")

start_date, end_date = (date_range if len(date_range) == 2 else (date.today() - timedelta(days=30), date.today()))
keyword = keyword_query.strip().lower()
filtered_articles = [
    article
    for article in articles
    if (not article.published_at or start_date <= article.published_at.astimezone().date() <= end_date)
    and (not keyword or keyword in f"{article.title} {article.summary}".lower())
]

if market_error:
    fallback_label = "마지막 성공 데이터를 표시합니다" if using_saved_snapshot else "샘플 데이터를 표시합니다"
    st.warning(f"주가 데이터를 불러오지 못했습니다. {fallback_label}: {market_error}")
if news_error:
    fallback_label = "마지막 성공 뉴스를 표시합니다" if using_saved_articles else "샘플 뉴스를 표시합니다"
    st.warning(f"뉴스를 불러오지 못했습니다. {fallback_label}: {news_error}")

st.subheader(f"{snapshot.name} ({snapshot.symbol})")
price_col, change_col, volume_col, time_col = st.columns(4)
price_col.metric("현재가", snapshot.price_display, snapshot.change_display)
change_col.metric("등락률", f"{snapshot.change_rate:+.2f}%")
volume_col.metric("거래량", f"{snapshot.volume:,}" if snapshot.volume else "-")
time_col.metric("데이터 기준 시각", format_time(snapshot.captured_at))

left, right = st.columns([2, 1])
with left:
    st.subheader(f"최근 뉴스 ({len(filtered_articles)}건)")
    if not filtered_articles:
        st.info("선택한 조건에 맞는 뉴스가 없습니다.")
    for article in filtered_articles[:10]:
        with st.container(border=True):
            st.markdown(f"**[{article.title}]({article.url})**")
            st.caption(f"{article.source} · {format_time(article.published_at)}")
            if article.summary:
                st.write(article.summary)
with right:
    st.subheader("주요 키워드")
    keywords = {}
    for article in filtered_articles:
        for keyword in article.keywords:
            keywords[keyword] = keywords.get(keyword, 0) + 1
    if keywords:
        for keyword, count in sorted(keywords.items(), key=lambda item: -item[1])[:8]:
            st.write(f"`{keyword}` × {count}")
    else:
        st.caption("키워드가 없습니다.")
    st.subheader("수집 상태")
    market_collection_status = load_collection_status("market", snapshot.symbol, market)
    news_collection_status = load_collection_status("news", snapshot.symbol, market)
    if market_collection_status and market_collection_status.status != "ok":
        st.error(f"주가 수집 실패 · {format_time(market_collection_status.last_attempt_at)}")
        if market_collection_status.last_success_at:
            st.caption(f"주가 마지막 성공: {format_time(market_collection_status.last_success_at)}")
    elif market_collection_status:
        st.success(f"주가 수집 성공 · {format_time(market_collection_status.last_success_at)}")
    if news_collection_status and news_collection_status.status != "ok":
        st.error(f"뉴스 수집 실패 · {format_time(news_collection_status.last_attempt_at)}")
        if news_collection_status.last_success_at:
            st.caption(f"뉴스 마지막 성공: {format_time(news_collection_status.last_success_at)}")
    elif news_collection_status:
        st.success(f"뉴스 {len(filtered_articles)}건 표시 · {format_time(news_collection_status.last_success_at)}")
    st.caption(f"조회 기준: {datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M')}")

if show_chart:
    st.subheader("최근 1개월 주가")
    try:
        history = load_price_history(snapshot.symbol, market)
        st.line_chart(history, y_label="가격")
    except Exception as exc:
        st.warning(f"차트 데이터를 불러오지 못했습니다: {exc}")
