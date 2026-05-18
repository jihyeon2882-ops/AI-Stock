from backend import get_classified_disclosures

# 기본값 테스트
result = get_classified_disclosures()
print(f"기본값 분류 완료: {len(result)}건")
for d in result:
    print(f"[{d['importance']}] {d['corp_name']} — {d['summary']} ({d['sentiment']})")

print("---")

# importance_rules 직접 전달 테스트
custom_rules = {
    "high": ["유상증자", "전환사채"],
    "mid": ["자기주식취득"],
    "low": ["사업보고서", "주주총회소집공고"]
}
result2 = get_classified_disclosures(importance_rules=custom_rules)
print(f"커스텀 분류 완료: {len(result2)}건")
for d in result2:
    print(f"[{d['importance']}] {d['corp_name']} — {d['summary']} ({d['sentiment']})")