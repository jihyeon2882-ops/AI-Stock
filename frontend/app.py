from datetime import date, datetime
from pathlib import Path
import sys

import streamlit as st

# frontend/app.py에서 backend 폴더를 import하기 위한 설정
ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend import get_classified_disclosures

# 10분 캐싱 함수
@st.cache_data(ttl=600)  
def get_cached_disclosures(date_str):
    return get_classified_disclosures(date=date_str)

# ==========================================
# 0. 입력 위젯 연동을 위한 세션 상태(Session State) 초기화
# ==========================================
if "search_date_input" not in st.session_state:
    st.session_state.search_date_input = date.today()
if "importance_filter_input" not in st.session_state:
    st.session_state.importance_filter_input = "전체"
if "sentiment_filter_input" not in st.session_state:
    st.session_state.sentiment_filter_input = "전체"
if "sort_input" not in st.session_state:
    st.session_state.sort_input = "기본순"
if "trigger_search" not in st.session_state:
    st.session_state.trigger_search = False

# ==========================================
# 1. 알림 보관함 장부(Session State) 생성 및 자동 저장 함수
# ==========================================
if "saved_alerts" not in st.session_state:
    st.session_state.saved_alerts = []

def auto_save_and_filter_new(high_disclosures):
    """중요 공시를 보관함에 즉시 자동 저장 (데모 버튼 전용)"""
    existing_nos = {item["rcept_no"] for item in st.session_state.saved_alerts}
    new_alerts = [d for d in high_disclosures if d["rcept_no"] not in existing_nos]
    if new_alerts:
        st.session_state.saved_alerts.extend(new_alerts)
    return new_alerts

# ==========================================
# 2. 팝업창(모달) UI 정의
# ==========================================
@st.dialog("🚨 중요 공시 알림")
def show_alert_popup(new_high_disclosures):
    st.error(f"**{len(new_high_disclosures)}건**의 새로운 중요 공시가 등록되어 보관함에 자동 저장되었습니다!", icon="🚨")
    for d in new_high_disclosures:
        st.markdown(f"- **{d.get('corp_name')}**: {d.get('report_nm')}")
    st.write("---")
    st.caption("💡 팝업창 바깥 영역이나 우측 상단의 X 버튼을 누르면 창이 닫힙니다.")

@st.dialog("🔔 내 알림 보관함")
def show_inbox_popup():
    if not st.session_state.saved_alerts:
        st.info("보관된 알림이 없습니다.")
    else:
        # [요구사항 3, 4] 리스트 내 버튼 및 X 버튼 레이아웃 구현
        for idx, d in enumerate(st.session_state.saved_alerts):
            col_item, col_del = st.columns([5, 1])
            
            with col_item:
                # 공시 정보 버튼화 (클릭 시 해당 날짜로 메인 화면 이동 및 자동 조회)
                try:
                    dt_obj = datetime.strptime(d.get('rcept_dt'), "%Y%m%d").date()
                except:
                    dt_obj = date.today()
                
                btn_label = f"🏢 {d.get('corp_name')} | {d.get('report_nm')}\n({d.get('rcept_dt')})"
                if st.button(btn_label, key=f"go_{d.get('rcept_no')}_{idx}", use_container_width=True):
                    st.session_state.search_date_input = dt_obj
                    st.session_state.importance_filter_input = "전체"  # 리스트에 확실히 보이도록 초기화
                    st.session_state.trigger_search = True            # 자동 조회 트리거 활성화
                    st.rerun()
            
            with col_del:
                # 개별 삭제 버튼
                if st.button("❌", key=f"del_{d.get('rcept_no')}_{idx}", use_container_width=True):
                    st.session_state.saved_alerts.pop(idx)
                    st.rerun()
            st.write("---")

# ==========================================
# 3. 상단 UI (타이틀 & 보관함 버튼)
# ==========================================
col_title, col_inbox = st.columns([4, 1])

with col_title:
    st.title("돈버는 공시 알리미")

with col_inbox:
    st.write(" ") 
    inbox_label = f"🔔 보관함 ({len(st.session_state.saved_alerts)})"
    if st.button(inbox_label, use_container_width=True):
        show_inbox_popup()

st.write("공시를 AI가 중요도와 영향도로 분류해드립니다.")

# --- 필터 설정 영역 (세션 상태와 key 파라미터로 동적 연동) ---
selected_date = st.date_input("조회할 날짜를 선택하세요.", key="search_date_input")
selected_importance = st.selectbox("중요도 필터", ["전체", "높음", "보통", "일반"], key="importance_filter_input")
selected_sentiment = st.selectbox("영향도 필터", ["전체", "긍정", "부정", "중립"], key="sentiment_filter_input")
selected_sort = st.selectbox("정렬 기준", ["기본순", "중요도 높은 순", "영향도 긍정 먼저", "영향도 부정 먼저"], key="sort_input")

date_str = selected_date.strftime("%Y%m%d")

# 매핑 딕셔너리
importance_map = {"high": "높음", "mid": "보통", "low": "일반"}
sentiment_map = {"pos": "긍정", "neg": "부정", "neu": "중립"}
importance_filter_map = {"높음": "high", "보통": "mid", "일반": "low"}
sentiment_filter_map = {"긍정": ["pos"], "부정": ["neg"], "중립": ["neu"]}
importance_order = {"high": 0, "mid": 1, "low": 2}
sentiment_positive_order = {"pos": 0, "neu": 1, "neg": 2}
sentiment_negative_order = {"neg": 0, "neu": 1, "pos": 2}

# --- 버튼 영역 ---
col_submit, col_refresh = st.columns([3, 1])

with col_submit:
    submit_clicked = st.button("공시 조회하기", type="primary", use_container_width=True)

with col_refresh:
    refresh_clicked = st.button("🔄 최신화", use_container_width=True)

if refresh_clicked:
    st.cache_data.clear()  
    st.toast("캐시가 완전히 초기화되었습니다! 이제 [공시 조회하기]를 누르면 실시간 데이터를 가져옵니다.")

# 보관함에서 공시를 선택해 이동한 경우, 조회를 자동으로 자동 수행합니다.
if st.session_state.trigger_search:
    submit_clicked = True
    st.session_state.trigger_search = False

# ==========================================
# 4. 공시 조회 및 분석 로직
# ==========================================
if submit_clicked:
    with st.spinner("공시를 조회하고 AI가 분석하는 중입니다..."):
        try:
            disclosures = get_cached_disclosures(date_str)
            # [요구사항 1] 공시 조회 시 보관함으로 들어가는 자동 저장 로직 완전 삭제
            
        except Exception as error:
            st.error(f"공시 조회 중 오류가 발생했습니다: {error}")
            disclosures = []

        # --- [요구사항 2] 선택한 날짜에 해당하는 공시만 노출되도록 필터링 보장 ---
        filtered_disclosures = [item for item in disclosures if item.get("rcept_dt") == date_str]

        # 필터 및 정렬 적용
        if selected_importance != "전체":
            selected_importance_code = importance_filter_map[selected_importance]
            filtered_disclosures = [item for item in filtered_disclosures if item.get("importance") == selected_importance_code]

        if selected_sentiment != "전체":
            selected_sentiment_codes = sentiment_filter_map[selected_sentiment]
            filtered_disclosures = [item for item in filtered_disclosures if item.get("sentiment") in selected_sentiment_codes]

        if selected_sort == "중요도 높은 순":
            filtered_disclosures = sorted(filtered_disclosures, key=lambda item: importance_order.get(item.get("importance"), 99))
        elif selected_sort == "영향도 긍정 먼저":
            filtered_disclosures = sorted(filtered_disclosures, key=lambda item: sentiment_positive_order.get(item.get("sentiment"), 99))
        elif selected_sort == "영향도 부정 먼저":
            filtered_disclosures = sorted(filtered_disclosures, key=lambda item: sentiment_negative_order.get(item.get("sentiment"), 99))

        # --- 결과 UI 출력 ---
        st.write(f"총 {len(filtered_disclosures)}건의 공시가 조회되었습니다.")

        # 지표 계산
        high_count = sum(1 for item in filtered_disclosures if item.get("importance") == "high")
        mid_count = sum(1 for item in filtered_disclosures if item.get("importance") == "mid")
        low_count = sum(1 for item in filtered_disclosures if item.get("importance") == "low")
        pos_count = sum(1 for item in filtered_disclosures if item.get("sentiment") == "pos")
        neg_count = sum(1 for item in filtered_disclosures if item.get("sentiment") == "neg")
        neu_count = sum(1 for item in filtered_disclosures if item.get("sentiment") == "neu")

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("전체 공시", f"{len(filtered_disclosures)}건")
        with col2: st.metric("높음", f"{high_count}건")
        with col3: st.metric("보통", f"{mid_count}건")
        with col4: st.metric("일반", f"{low_count}건")

        col1, col2, col3 = st.columns(3)
        with col1: st.metric("긍정", f"{pos_count}건")
        with col2: st.metric("부정", f"{neg_count}건")
        with col3: st.metric("중립", f"{neu_count}건")

        if len(filtered_disclosures) == 0:
            st.info("조회된 공시가 없거나 조건에 맞는 공시가 없습니다.")

        for item in filtered_disclosures:
            importance = item.get("importance", "low")
            importance_text = importance_map.get(importance, "일반")
            sentiment_text = sentiment_map.get(item.get("sentiment"), item.get("sentiment", "-"))

            with st.container(border=True):
                if importance == "high":
                    badge_color, text_color = "#ff4b4b", "white"
                elif importance == "mid":
                    badge_color, text_color = "#ffc107", "black"
                else:
                    badge_color, text_color = "#e0e4e8", "black"

                badge_html = f"""
                <span style="
                    background-color: {badge_color}; 
                    color: {text_color}; 
                    padding: 0.2rem 0.6rem; 
                    border-radius: 0.5rem; 
                    font-size: 0.85rem; 
                    font-weight: 600; 
                    margin-right: 0.5rem;
                ">
                    {importance_text}
                </span>
                """

                report_nm = item.get("report_nm", "공시명 없음")
                st.markdown(f"{badge_html} **{report_nm}**", unsafe_allow_html=True)
                st.write(f"🏢 **회사명:** {item.get('corp_name', '-')}")
                st.write(f"📅 **접수일자:** {item.get('rcept_dt', '-')}")
                st.write(f"🤖 **AI 요약:** {item.get('summary', '요약 없음')} (영향도: {sentiment_text})")

                rcept_no = item.get("rcept_no", "")
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(f"접수번호: {rcept_no}")
                with col2:
                    if rcept_no:
                        dart_url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"
                        st.link_button("📄 DART 원문", dart_url, use_container_width=True)

# ==========================================
# 5. 시연용 (디버그) 버튼 노출
# ==========================================
st.write("")
st.write("")
st.write("") 

st.caption("시연용 디버그 도구입니다.")
if st.button("🚨 중요 공시(High) 강제 발생", use_container_width=True):
    # 시연용 가짜 데이터 생성
    demo_high_disclosure = [
        {
            "rcept_no": "99999999999999",
            "corp_name": "데모주식회사",
            "report_nm": "[시연용] 대규모 유상증자 결정 (주주배정)",
            "rcept_dt": date_str,
            "importance": "high"
        }
    ]
    # 데모 버튼을 누를 때만 보관함 자동 저장 및 팝업 활성화가 일어납니다.
    new_demo = auto_save_and_filter_new(demo_high_disclosure)
    if new_demo:
        show_alert_popup(new_demo)
    else:
        st.toast("⚠️ 해당 데모 공시는 이미 발생하여 보관함에 들어가 있습니다. (중복 팝업 차단)")