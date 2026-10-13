"""수동 DART/Gemini 확인. 자동 테스트는 tests/에서 외부 호출 없이 실행한다."""

from backend import get_classified_disclosures
from backend.dart_client import DisclosureFetchError


def main():
    try:
        result = get_classified_disclosures()
    except DisclosureFetchError as error:
        raise SystemExit(str(error)) from None
    print(f"조회 완료: {len(result)}건")
    for item in result:
        print(f"[{item['importance'] or '미분류'}] {item['corp_name']} — {item['summary']}")


if __name__ == "__main__":
    main()
