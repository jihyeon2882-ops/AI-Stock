# 로컬 개발 시 .streamlit/secrets.toml에 아래 내용 추가
# OPENAI_API_KEY = "your_openai_api_key_here"
#
# 배포 시 Streamlit Community Cloud 대시보드 > Secrets에 동일 내용 입력
# .streamlit/secrets.toml은 .gitignore에 반드시 추가

import copy
import json

import streamlit as st
from openai import OpenAI

OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")

_SYSTEM_PROMPT = """
너는 한국 주식 공시 분석 전문가야.
아래 공시 목록을 분석해서 JSON 형식으로만 응답해.
다른 텍스트는 절대 포함하지 마.

응답 형식:
{"results": [{"rcept_no": "...", "importance": "...", "summary": "...", "sentiment": "..."}, ...]}

중요도(importance) 기준:
- high: 유상증자, 전환사채, 최대주주변경, 관리종목지정, 상장폐지, 자기자본 10% 이상 대형계약
- mid: 자기주식취득·처분, 임원변경, 분기·반기 실적공시, 소형계약
- low: 정기공시(사업보고서 등), 단순공고, 주주총회소집, 기타 법정의무공시

요약(summary) 기준:
- 30자 이내 한국어 1줄 요약
- 투자 판단을 유도하는 표현(매수·매도·호재·악재) 사용 금지
- 관리종목·상장폐지 등 법적 표현은 임의 변환 금지

영향도(sentiment) 기준:
- pos: 대형 계약 체결, 자사주 취득 등 주가에 긍정적 영향 가능성
- neg: 유상증자, 관리종목 지정 등 주가에 부정적 영향 가능성
- neu: 정기 공시, 임원 변경 등 중립적 공시
"""

_DEFAULT = {"importance": "low", "summary": "요약 실패", "sentiment": "neu"}


def _apply_defaults(results: list[dict]) -> None:
    for item in results:
        item.update(_DEFAULT)


def classify_disclosures(disclosures: list[dict]) -> list[dict]:
    results = copy.deepcopy(disclosures)

    user_payload = [
        {
            "rcept_no": d["rcept_no"],
            "corp_name": d["corp_name"],
            "report_nm": d["report_nm"],
        }
        for d in disclosures
    ]

    client = OpenAI(api_key=OPENAI_API_KEY)

    # --- GPT 호출 ---
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
        )
        raw_content = response.choices[0].message.content
        if raw_content is None:
            print("[WARN] GPT 응답 내용이 비어 있습니다, 전체 기본값으로 대체합니다.")
            _apply_defaults(results)
            return results
        
    except Exception as exc:
        print(f"[WARN] GPT 호출 실패, 전체 기본값으로 대체합니다: {exc}")
        _apply_defaults(results)
        return results

    # --- JSON 파싱 ---
    try:
        gpt_data = json.loads(raw_content)
        gpt_results: list[dict] = gpt_data["results"]
    except Exception as exc:
        print(f"[WARN] GPT 응답 파싱 실패, 전체 기본값으로 대체합니다: {exc}")
        _apply_defaults(results)
        return results

    # --- rcept_no 기준 매핑 ---
    gpt_map = {item["rcept_no"]: item for item in gpt_results}

    for item in results:
        matched = gpt_map.get(item["rcept_no"])
        if matched is None:
            item.update(_DEFAULT)
        else:
            item["importance"] = matched.get("importance", _DEFAULT["importance"])
            item["summary"] = matched.get("summary", _DEFAULT["summary"])
            item["sentiment"] = matched.get("sentiment", _DEFAULT["sentiment"])

    return results
