from datetime import date
from pathlib import Path
import sys

import streamlit as st


# frontend/app.py에서 backend 폴더를 import하기 위한 설정
ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend import get_classified_disclosures


st.title("돈버는 공시 알리미")

st.write("공시를 AI가 중요도와 영향도로 분류해드립니다.")


# 날짜 선택
selected_date = st.date_input(
    "조회할 날짜를 선택하세요.",
    value=date.today(),
)

# 중요도 필터
selected_importance = st.selectbox(
    "중요도 필터",
    ["전체", "높음", "보통", "낮음"],
)

# 영향도 필터
selected_sentiment = st.selectbox(
    "영향도 필터",
    ["전체", "긍정", "부정", "중립"],
)

# 정렬 기준
selected_sort = st.selectbox(
    "정렬 기준",
    ["기본순", "중요도 높은 순", "영향도 긍정 먼저", "영향도 부정 먼저"],
)


# 선택한 날짜를 백엔드 함수에 넘길 YYYYMMDD 형식으로 변환
date_str = selected_date.strftime("%Y%m%d")


# 화면 표시용 한글 변환표
importance_map = {
    "high": "높음",
    "mid": "보통",
    "low": "낮음",
}

sentiment_map = {
    "pos": "긍정",
    "neg": "부정",
    "neu": "중립",
}


# 필터 변환표
importance_filter_map = {
    "높음": "high",
    "보통": "mid",
    "낮음": "low",
}

sentiment_filter_map = {
    "긍정": ["pos"],
    "부정": ["neg"],
    "중립": ["neu"],
}


# 정렬 기준표
importance_order = {
    "high": 0,
    "mid": 1,
    "low": 2,
}

sentiment_positive_order = {
    "pos": 0,
    "neu": 1,
    "neg": 2,
}

sentiment_negative_order = {
    "neg": 0,
    "neu": 1,
    "pos": 2,
}


if st.button("공시 조회하기"):

    with st.spinner("공시를 조회하고 AI가 분석하는 중입니다..."):

        # 백엔드 최신 함수 호출
        try:
            disclosures = get_classified_disclosures(date=date_str)

        except Exception as error:
            st.error(f"공시 조회 중 오류가 발생했습니다: {error}")
            disclosures = []

        # 중요도 필터와 영향도 필터를 순서대로 적용
        filtered_disclosures = disclosures

        if selected_importance != "전체":
            selected_importance_code = importance_filter_map[selected_importance]
            filtered_disclosures = [
                item
                for item in filtered_disclosures
                if item.get("importance") == selected_importance_code
            ]

        if selected_sentiment != "전체":
            selected_sentiment_codes = sentiment_filter_map[selected_sentiment]
            filtered_disclosures = [
                item
                for item in filtered_disclosures
                if item.get("sentiment") in selected_sentiment_codes
            ]

        # 정렬 적용
        if selected_sort == "중요도 높은 순":
            filtered_disclosures = sorted(
                filtered_disclosures,
                key=lambda item: importance_order.get(item.get("importance"), 99),
            )

        elif selected_sort == "영향도 긍정 먼저":
            filtered_disclosures = sorted(
                filtered_disclosures,
                key=lambda item: sentiment_positive_order.get(item.get("sentiment"), 99),
            )

        elif selected_sort == "영향도 부정 먼저":
            filtered_disclosures = sorted(
                filtered_disclosures,
                key=lambda item: sentiment_negative_order.get(item.get("sentiment"), 99),
            )

    st.write(f"총 {len(filtered_disclosures)}건의 공시가 조회되었습니다.")

    # 중요도 요약 지표
    high_count = sum(1 for item in filtered_disclosures if item.get("importance") == "high")
    mid_count = sum(1 for item in filtered_disclosures if item.get("importance") == "mid")
    low_count = sum(1 for item in filtered_disclosures if item.get("importance") == "low")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("전체 공시", f"{len(filtered_disclosures)}건")

    with col2:
        st.metric("높음", f"{high_count}건")

    with col3:
        st.metric("보통", f"{mid_count}건")

    with col4:
        st.metric("낮음", f"{low_count}건")

    # 영향도 요약 지표
    pos_count = sum(1 for item in filtered_disclosures if item.get("sentiment") == "pos")
    neg_count = sum(1 for item in filtered_disclosures if item.get("sentiment") == "neg")
    neu_count = sum(1 for item in filtered_disclosures if item.get("sentiment") == "neu")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("긍정", f"{pos_count}건")

    with col2:
        st.metric("부정", f"{neg_count}건")

    with col3:
        st.metric("중립", f"{neu_count}건")

    # 결과 없음 처리
    if len(filtered_disclosures) == 0:
        st.info("조회된 공시가 없거나 조건에 맞는 공시가 없습니다.")

    # 공시 카드 출력
    for item in filtered_disclosures:
        importance_text = importance_map.get(item.get("importance"), item.get("importance", "-"))
        sentiment_text = sentiment_map.get(item.get("sentiment"), item.get("sentiment", "-"))

        with st.container(border=True):
            st.subheader(item.get("report_nm", "공시명 없음"))

            st.write(f"회사명: {item.get('corp_name', '-')}")
            st.write(f"접수일자: {item.get('rcept_dt', '-')}")
            st.write(f"AI 요약: {item.get('summary', '요약 없음')}")

            # 중요도 색상 표시
            if item.get("importance") == "high":
                st.error(f"중요도: {importance_text}")
            elif item.get("importance") == "mid":
                st.warning(f"중요도: {importance_text}")
            else:
                st.info(f"중요도: {importance_text}")

            # 영향도 색상 표시
            if item.get("sentiment") == "pos":
                st.success(f"영향도: {sentiment_text}")
            elif item.get("sentiment") == "neg":
                st.error(f"영향도: {sentiment_text}")
            else:
                st.info(f"영향도: {sentiment_text}")

            rcept_no = item.get("rcept_no", "")

            st.caption(f"접수번호: {rcept_no}")

            if rcept_no:
                dart_url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"
                st.link_button("DART 원문 보기", dart_url)