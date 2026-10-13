from datetime import datetime
from zoneinfo import ZoneInfo
import requests

from backend.config import get_setting

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

class DisclosureFetchError(RuntimeError):
    """실데이터를 확보하지 못한 조회. 샘플로 대체하지 않는다."""


def _fetch_from_dart(date: str) -> list[dict]:
    api_key = get_setting("DART_API_KEY")
    if not api_key:
        raise DisclosureFetchError("DART_API_KEY를 환경변수 또는 Streamlit Secrets에 설정해 주세요.")

    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        "crtfc_key": api_key,
        "bgn_de": date,
        "end_de": date,
        "page_count": 100,
        "page_no": 1,
    }
    results: dict[str, dict] = {}
    while True:
        try:
            response = requests.get(url, params=dict(params), timeout=10)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError):
            # HTTPError에는 인증키를 포함한 URL이 들어갈 수 있어 원문을 표시하지 않는다.
            raise DisclosureFetchError("DART 연결에 실패했습니다. 잠시 후 다시 조회해 주세요.") from None

        if not isinstance(data, dict):
            raise DisclosureFetchError("DART 응답 형식이 올바르지 않습니다.")
        status = data.get("status")
        if status == "013" and params["page_no"] == 1:
            return []
        if status != "000":
            messages = {
                "010": "등록되지 않은 DART 인증키입니다.",
                "011": "사용 중지된 DART 인증키입니다.",
                "012": "DART에서 허용되지 않은 IP입니다.",
                "020": "DART 요청 한도를 초과했습니다.",
                "800": "DART 시스템 점검 중입니다.",
            }
            raise DisclosureFetchError(messages.get(status, "DART 조회를 완료하지 못했습니다."))
        try:
            total_page = int(data["total_page"])
            items = data["list"]
            if not isinstance(items, list) or total_page < params["page_no"]:
                raise ValueError
            for item in items:
                record = {key: item[key] for key in ("rcept_no", "corp_name", "report_nm", "rcept_dt")}
                if not all(isinstance(value, str) and value for value in record.values()):
                    raise ValueError
                if not (len(record["rcept_no"]) == 14 and record["rcept_no"].isascii() and record["rcept_no"].isdigit()):
                    raise ValueError
                record.update(importance=None, summary=None, sentiment=None, data_source="dart")
                results[record["rcept_no"]] = record
        except (KeyError, TypeError, ValueError):
            raise DisclosureFetchError("DART 응답 형식이 올바르지 않습니다.") from None
        if params["page_no"] >= total_page:
            return list(results.values())
        params["page_no"] += 1

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
            "data_source": "sample",
        })
    return results

def get_disclosures(date: str | None = None) -> list[dict]:
    if date is None:
        date = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")

    if not isinstance(date, str) or len(date) != 8 or not date.isascii() or not date.isdigit():
        raise ValueError("날짜는 YYYYMMDD 형식이어야 합니다.")
    datetime.strptime(date, "%Y%m%d")

    if USE_SAMPLE_DATA:
        return _sample_for_date(date)

    return _fetch_from_dart(date)
