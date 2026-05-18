from datetime import date

import streamlit as st


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

# 선택한 날짜를 DART 조회에 사용할 수 있는 YYYYMMDD 형식으로 변환합니다.
date_str = selected_date.strftime("%Y%m%d")

# 화면에 표시할 한글 라벨입니다.
importance_map = {
    "high": "높음",
    "mid": "보통",
    "low": "낮음",
}

sentiment_map = {
    "pos": "긍정",
    "neg": "부정",
    "neu": "중립",
    "neub": "중립",
}

# 중요도 필터 변환표
importance_filter_map = {
    "높음": "high",
    "보통": "mid",
    "낮음": "low",
}

# 영향도 필터 변환표
sentiment_filter_map = {
    "긍정": ["pos"],
    "부정": ["neg"],
    "중립": ["neu", "neub"],
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
    "neub": 1,
    "neg": 2,
}

sentiment_negative_order = {
    "neg": 0,
    "neu": 1,
    "neub": 1,
    "pos": 2,
}

# 조회 버튼
if st.button("공시 조회하기"):

    # 실제 백엔드/API 연결 시 시간이 걸릴 수 있으므로 로딩 표시를 보여줍니다.
    with st.spinner("공시를 조회하고 AI가 분석하는 중입니다..."):
        st.write(f"{date_str} 날짜의 공시를 조회합니다.")

        # 임시 공시 데이터입니다.
        # 아직 backend 연결 전이므로 화면 테스트용으로 사용합니다.
        disclosures = [
            {
                "rcept_no": "20250518000123",
                "corp_name": "삼성전자",
                "report_nm": "유상증자 결정",
                "rcept_dt": date_str,
                "importance": "high",
                "summary": "삼성전자, 유상증자 결정",
                "sentiment": "neg",
            },
            {
                "rcept_no": "20250518000456",
                "corp_name": "카카오",
                "report_nm": "단일판매 공급계약 체결",
                "rcept_dt": date_str,
                "importance": "mid",
                "summary": "카카오, 공급계약 체결",
                "sentiment": "pos",
            },
            {
                "rcept_no": "20250518000789",
                "corp_name": "네이버",
                "report_nm": "분기보고서",
                "rcept_dt": date_str,
                "importance": "low",
                "summary": "네이버, 분기보고서 제출",
                "sentiment": "neu",
            },
        ]

        # 중요도 필터와 영향도 필터를 순서대로 적용합니다.
        filtered_disclosures = disclosures

        if selected_importance != "전체":
            selected_importance_code = importance_filter_map[selected_importance]
            filtered_disclosures = [
                item
                for item in filtered_disclosures
                if item["importance"] == selected_importance_code
            ]

        if selected_sentiment != "전체":
            selected_sentiment_codes = sentiment_filter_map[selected_sentiment]
            filtered_disclosures = [
                item
                for item in filtered_disclosures
                if item["sentiment"] in selected_sentiment_codes
            ]

        # 선택한 정렬 기준에 따라 공시 목록을 정렬합니다.
        if selected_sort == "중요도 높은 순":
            filtered_disclosures = sorted(
                filtered_disclosures,
                key=lambda item: importance_order.get(item["importance"], 99),
            )

        elif selected_sort == "영향도 긍정 먼저":
            filtered_disclosures = sorted(
                filtered_disclosures,
                key=lambda item: sentiment_positive_order.get(item["sentiment"], 99),
            )

        elif selected_sort == "영향도 부정 먼저":
            filtered_disclosures = sorted(
                filtered_disclosures,
                key=lambda item: sentiment_negative_order.get(item["sentiment"], 99),
            )

    # 로딩이 끝난 뒤 결과를 보여줍니다.
    st.write(f"총 {len(filtered_disclosures)}건의 공시가 조회되었습니다.")

# 조회 결과 요약 지표
    high_count = sum(1 for item in filtered_disclosures if item["importance"] == "high")
    mid_count = sum(1 for item in filtered_disclosures if item["importance"] == "mid")
    low_count = sum(1 for item in filtered_disclosures if item["importance"] == "low")

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
    pos_count = sum(1 for item in filtered_disclosures if item["sentiment"] == "pos")
    neg_count = sum(1 for item in filtered_disclosures if item["sentiment"] == "neg")
    neu_count = sum(
        1
        for item in filtered_disclosures
        if item["sentiment"] in ["neu", "neub"]
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("긍정", f"{pos_count}건")

    with col2:
        st.metric("부정", f"{neg_count}건")

    with col3:
        st.metric("중립", f"{neu_count}건")

    # 필터링 결과가 없을 때 안내 메시지
    if len(filtered_disclosures) == 0:
        st.info("조건에 맞는 공시가 없습니다.")

    # 공시 카드 출력
    for item in filtered_disclosures:
        importance_text = importance_map.get(item["importance"], item["importance"])
        sentiment_text = sentiment_map.get(item["sentiment"], item["sentiment"])

        with st.container(border=True):
            st.subheader(item["report_nm"])
            st.write(f"회사명: {item['corp_name']}")
            st.write(f"접수일자: {item['rcept_dt']}")

            # 중요도 색상 표시
            if item["importance"] == "high":
                st.error(f"중요도: {importance_text}")
            elif item["importance"] == "mid":
                st.warning(f"중요도: {importance_text}")
            else:
                st.info(f"중요도: {importance_text}")

            # 영향도 색상 표시
            if item["sentiment"] == "pos":
                st.success(f"영향도: {sentiment_text}")
            elif item["sentiment"] == "neg":
                st.error(f"영향도: {sentiment_text}")
            else:
                st.info(f"영향도: {sentiment_text}")

            st.write(f"AI 요약: {item['summary']}")
            st.caption(f"접수번호: {item['rcept_no']}")

            dart_url = (
                "https://dart.fss.or.kr/dsaf001/main.do"
                f"?rcpNo={item['rcept_no']}"
            )

            st.link_button("DART 원문 보기", dart_url)  