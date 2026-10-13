"""수동 Gemini 연결 확인: GEMINI_API_KEY 설정 후 python test.py (실제 API 호출)."""

from backend.config import get_setting
from google import genai


def main():
    api_key = get_setting("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY를 환경변수 또는 Streamlit Secrets에 설정해 주세요.")
    try:
        with genai.Client(api_key=api_key) as client:
            response = client.models.generate_content(
                model=get_setting("GEMINI_MODEL", "gemini-2.5-flash-lite"),
                contents="공시 요약 연결 확인입니다. 확인이라고 답해 주세요.",
            )
            print("연결 성공" if response.text else "빈 응답")
    except Exception:
        raise SystemExit("연결 실패. 키 권한·모델·할당량을 확인해 주세요.") from None


if __name__ == "__main__":
    main()
