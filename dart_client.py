# 로컬 개발 시 .streamlit/secrets.toml에 아래 내용 추가
# [secrets]
# DART_API_KEY = "your_dart_api_key_here"
#
# 배포 시 Streamlit Community Cloud 대시보드 > Secrets에 동일 내용 입력
# .streamlit/secrets.toml은 .gitignore에 반드시 추가

from datetime import datetime

import requests
import streamlit as st

USE_SAMPLE_DATA = True

DART_API_KEY = st.secrets.get("DART_API_KEY")

# DART API 엔드포인트
# URL: https://opendart.fss.or.kr/api/list.json
# 파라미터: crtfc_key, bgn_de, end_de, pblntf_ty=A, page_count=100

_SAMPLE_DISCLOSURES = [
    # --- high importance ---
    {
        "rcept_no": "20260518000001",
        "corp_name": "삼성전자",
        "report_nm": "유상증자결정(주주배정후실권주일반공모)",
        "rcept_dt": "20260518",
    },
    {
        "rcept_no": "20260518000002",
        "corp_name": "LG에너지솔루션",
        "report_nm": "전환사채권발행결정",
        "rcept_dt": "20260518",
    },
    {
        "rcept_no": "20260518000003",
        "corp_name": "카카오",
        "report_nm": "최대주주변경을수반하는주식담보제공계약체결",
        "rcept_dt": "20260518",
    },
    {
        "rcept_no": "20260518000004",
        "corp_name": "현대차",
        "report_nm": "최대주주변경",
        "rcept_dt": "20260518",
    },
    {
        "rcept_no": "20260518000005",
        "corp_name": "SK하이닉스",
        "report_nm": "유상증자결정(제3자배정)",
        "rcept_dt": "20260518",
    },
    # --- mid importance ---
    {
        "rcept_no": "20260518000006",
        "corp_name": "NAVER",
        "report_nm": "단일판매·공급계약체결(대규모기업집단)",
        "rcept_dt": "20260518",
    },
    {
        "rcept_no": "20260518000007",
        "corp_name": "셀트리온",
        "report_nm": "단일판매·공급계약체결(대규모기업집단)",
        "rcept_dt": "20260518",
    },
    {
        "rcept_no": "20260518000008",
        "corp_name": "포스코홀딩스",
        "report_nm": "자기주식취득결정",
        "rcept_dt": "20260518",
    },
    {
        "rcept_no": "20260518000009",
        "corp_name": "KB금융",
        "report_nm": "자기주식취득결정",
        "rcept_dt": "20260518",
    },
    {
        "rcept_no": "20260518000010",
        "corp_name": "LG화학",
        "report_nm": "임원·주요주주특정증권등소유상황보고서",
        "rcept_dt": "20260518",
    },
    # --- low importance ---
    {
        "rcept_no": "20260518000011",
        "corp_name": "기아",
        "report_nm": "단일판매·공급계약체결",
        "rcept_dt": "20260518",
    },
    {
        "rcept_no": "20260518000012",
        "corp_name": "삼성바이오로직스",
        "report_nm": "분기보고서 (2026.03)",
        "rcept_dt": "20260518",
    },
    {
        "rcept_no": "20260518000013",
        "corp_name": "SK텔레콤",
        "report_nm": "사업보고서 (2025.12)",
        "rcept_dt": "20260518",
    },
    {
        "rcept_no": "20260518000014",
        "corp_name": "롯데케미칼",
        "report_nm": "주주총회소집공고",
        "rcept_dt": "20260518",
    },
    {
        "rcept_no": "20260518000015",
        "corp_name": "한화에어로스페이스",
        "report_nm": "임원변경",
        "rcept_dt": "20260518",
    },
    {
        "rcept_no": "20260518000016",
        "corp_name": "두산에너빌리티",
        "report_nm": "분기보고서 (2026.03)",
        "rcept_dt": "20260518",
    },
]


def _attach_defaults(raw: dict, date: str) -> dict:
    return {
        "rcept_no": raw["rcept_no"],
        "corp_name": raw["corp_name"],
        "report_nm": raw["report_nm"],
        "rcept_dt": raw.get("rcept_dt", date),
        "importance": None,
        "summary": None,
        "sentiment": None,
    }


def _fetch_from_dart(date: str) -> list[dict]:
    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "bgn_de": date,
        "end_de": date,
        "pblntf_ty": "A",
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
    return [_attach_defaults(item, date) for item in _SAMPLE_DISCLOSURES]


def get_disclosures(date: str | None) -> list[dict]:
    if date is None:
        date = datetime.today().strftime("%Y%m%d")

    if USE_SAMPLE_DATA:
        return _sample_for_date(date)

    try:
        return _fetch_from_dart(date)
    except Exception as exc:
        print(f"[WARN] DART API 호출 실패, 샘플 데이터로 대체합니다: {exc}")
        return _sample_for_date(date)
