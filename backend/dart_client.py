from datetime import datetime
import requests
import streamlit as st

USE_SAMPLE_DATA = False

_SAMPLE_DISCLOSURES = [
    {"rcept_no": "20260518000001", "corp_name": "삼성전자", "report_nm": "유상증자결정(주주배정후실권주일반공모)"},
    {"rcept_no": "20260518000002", "corp_name": "LG에너지솔루션", "report_nm": "전환사채권발행결정"},
    {"rcept_no": "20260518000003", "corp_name": "카카오", "report_nm": "최대주주변경을수반하는주식담보제공계약체결"},
    {"rcept_no": "20260518000004", "corp_name": "현대차", "report_nm": "최대주주변경"},
    {"rcept_no": "20260518000005", "corp_name": "SK하이닉스", "report_nm": "유상증자결정(제3자배정)"},
    {"rcept_no": "20260518000006", "corp_name": "NAVER", "report_nm": "단일판매·공급계약체결(대규모기업집단)"},
    {"rcept_no": "20260518000007", "corp_name": "셀트리온", "report_nm": "단일판매·공급계약체결(대규모기업집단)"},
    {"rcept_no": "20260518000008", "corp_name": "포스코홀딩스", "report_nm": "자기주식취득결정"},
    {"rcept_no": "20260518000009", "corp_name": "KB금융", "report_nm": "자기주식취득결정"},
    {"rcept_no": "20260518000010", "corp_name": "LG화학", "report_nm": "임원·주요주주특정증권등소유상황보고서"},
    {"rcept_no": "20260518000011", "corp_name": "기아", "report_nm": "단일판매·공급계약체결"},
    {"rcept_no": "20260518000012", "corp_name": "삼성바이오로직스", "report_nm": "분기보고서 (2026.03)"},
    {"rcept_no": "20260518000013", "corp_name": "SK텔레콤", "report_nm": "사업보고서 (2025.12)"},
    {"rcept_no": "20260518000014", "corp_name": "롯데케미칼", "report_nm": "주주총회소집공고"},
    {"rcept_no": "20260518000015", "corp_name": "한화에어로스페이스", "report_nm": "임원변경"},
    {"rcept_no": "20260518000016", "corp_name": "두산에너빌리티", "report_nm": "분기보고서 (2026.03)"},
]

def _fetch_from_dart(date: str) -> list[dict]:
    # 💡 [수정] DART 키를 함수 실행 시점에 안전하게 가져옵니다.
    DART_API_KEY = st.secrets.get("DART_API_KEY")
    
    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "bgn_de": date,
        "end_de": date,
        "page_count": 100,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    if data.get("status") != "000":
        raise ValueError(f"DART API 오류: {data.get('message', '알 수 없는 오류')}")

    items = data.get("list", [])
    return [
        {
            "rcept_no": item["rcept_no"],
            "corp_name": item["corp_name"],
            "report_nm": item["report_nm"],
            "rcept_dt": item["rcept_dt"],
            "importance": None,
            "summary": None,
            "sentiment": None,
        }
        for item in items
    ]

def _sample_for_date(date: str) -> list[dict]:
    # 💡 [수정] 샘플 데이터의 날짜를 사용자가 UI에서 선택한 날짜로 강제 동기화합니다.
    results = []
    for item in _SAMPLE_DISCLOSURES:
        results.append({
            "rcept_no": item["rcept_no"],
            "corp_name": item["corp_name"],
            "report_nm": item["report_nm"],
            "rcept_dt": date,  # <-- 하드코딩된 날짜 대신 파라미터 날짜 대입
            "importance": None,
            "summary": None,
            "sentiment": None,
        })
    return results

def get_disclosures(date: str | None = None) -> list[dict]:
    if date is None:
        date = datetime.today().strftime("%Y%m%d")

    if USE_SAMPLE_DATA:
        return _sample_for_date(date)

    try:
        return _fetch_from_dart(date)
    except Exception as exc:
        print(f"[WARN] DART API 호출 실패, 샘플 데이터로 대체합니다: {exc}")
        return _sample_for_date(date)