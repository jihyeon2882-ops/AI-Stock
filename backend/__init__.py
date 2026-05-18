# 사용 예시 (app.py에서)
# from backend import get_classified_disclosures
# disclosures = get_classified_disclosures()
# disclosures = get_classified_disclosures(date="20260518")

from backend.dart_client import get_disclosures
from backend.llm_classifier import classify_disclosures

__all__ = ["get_classified_disclosures"]


def get_classified_disclosures(date: str | None = None) -> list[dict]:
    disclosures = get_disclosures(date)
    if not disclosures:
        return []
    return classify_disclosures(disclosures)
