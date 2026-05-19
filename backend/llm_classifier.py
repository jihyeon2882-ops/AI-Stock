import copy
import json
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Literal

_DEFAULT_IMPORTANCE_RULES: dict[str, list[str]] = {
    "high": ["유상증자", "전환사채", "최대주주변경", "관리종목지정", "상장폐지", "자기자본 10% 이상 대형계약"],
    "mid": ["자기주식취득·처분", "임원변경", "분기·반기 실적공시", "소형계약"],
    "low": ["정기공시(사업보고서 등)", "단순공고", "주주총회소집", "기타 법정의무공시"],
}

_SYSTEM_PROMPT_TEMPLATE = """
너는 한국 주식 공시 분석 전문가야.
아래 공시 목록을 분석해서 지정된 JSON 형식으로만 응답해.

{importance_section}

요약(summary) 기준:
- 30자 이내 한국어 1줄 요약
- 투자 판단을 유도하는 표현(매수·매도·호재·악재) 사용 금지

영향도(sentiment) 기준:
- pos: 주가에 긍정적 영향 가능성
- neg: 주가에 부정적 영향 가능성
- neu: 중립적 공시
"""

_DEFAULT = {"importance": "low", "summary": "요약 실패", "sentiment": "neu"}

# Pydantic을 활용해 Gemini가 정확한 JSON 구조로 응답하도록 강제합니다.
class DisclosureResult(BaseModel):
    rcept_no: str
    importance: Literal["high", "mid", "low"]
    summary: str
    sentiment: Literal["pos", "neg", "neu"]

class DisclosureResponse(BaseModel):
    results: list[DisclosureResult]


def _build_system_prompt(rules: dict[str, list[str]]) -> str:
    lines = ["중요도(importance) 기준:"]
    for level in ("high", "mid", "low"):
        keywords = rules.get(level, [])
        lines.append(f"- {level}: {', '.join(keywords)}")
    importance_section = "\n".join(lines)
    return _SYSTEM_PROMPT_TEMPLATE.format(importance_section=importance_section)


def _apply_defaults(results: list[dict]) -> None:
    for item in results:
        item.update(_DEFAULT)


def classify_disclosures(
    disclosures: list[dict],
    importance_rules: dict[str, list[str]] | None = None,
) -> list[dict]:
    
    # 💡 [핵심 수정] Streamlit Cloud 환경에서는 반드시 함수 호출 시점에 키를 가져와야 안전합니다.
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

    if not GEMINI_API_KEY:
        # 화면에 명확하게 에러를 띄웁니다.
        st.error("🚨 에러: Streamlit Secrets에 GEMINI_API_KEY가 등록되지 않았습니다.")
        results = copy.deepcopy(disclosures)
        _apply_defaults(results)
        return results

    rules = importance_rules if importance_rules else _DEFAULT_IMPORTANCE_RULES
    system_prompt = _build_system_prompt(rules)
    results = copy.deepcopy(disclosures)

    user_payload = [
        {"rcept_no": d["rcept_no"], "corp_name": d["corp_name"], "report_nm": d["report_nm"]}
        for d in disclosures
    ]

    # --- Gemini 호출 ---
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=json.dumps(user_payload, ensure_ascii=False),
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=DisclosureResponse, # 스키마 강제 규칙
                temperature=0.1
            ),
        )
        raw_content = response.text
        
    except Exception as exc:
        # 이제 에러가 나면 붉은 창으로 진짜 원인을 화면에 보여줍니다.
        st.error(f"🚨 Gemini API 호출 에러 발생: {exc}")
        _apply_defaults(results)
        return results

    # --- JSON 파싱 및 매핑 ---
    try:
        gpt_data = json.loads(raw_content)
        gpt_results: list[dict] = gpt_data["results"]
    except Exception as exc:
        st.error(f"🚨 JSON 파싱 에러 발생: {exc}")
        _apply_defaults(results)
        return results

    # ... (생략) ...
    gpt_map = {item["rcept_no"]: item for item in gpt_results}
    for item in results:
        matched = gpt_map.get(item["rcept_no"])
        if matched is None:
            item.update(_DEFAULT)
        else:
            # 💡 [수정] 대문자나 띄어쓰기가 섞여도 강제로 소문자/공백제거 처리
            item["importance"] = str(matched.get("importance", "low")).strip().lower()
            item["summary"] = str(matched.get("summary", "요약 실패"))
            item["sentiment"] = str(matched.get("sentiment", "neu")).strip().lower()

    return results