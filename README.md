# AI-Stock · 공시 알리미

DART에서 선택한 날짜의 공시 목록을 조회하고 Gemini로 **회사명·공시 제목**을 분류하는 Streamlit 앱입니다. 공시 본문을 가져오는 기능은 없으므로 금액·조건·실적 확인은 DART 원문을 이용합니다.

## 실행

Python 3.11 이상이 필요합니다. 저장소 루트에서 실행합니다.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run frontend/app.py
```

`.streamlit/secrets.toml.example`을 `.streamlit/secrets.toml`로 복사하고 `DART_API_KEY`, `GEMINI_API_KEY`를 입력하세요. Streamlit Community Cloud에서는 앱 설정의 Secrets에 같은 항목을 등록합니다. 환경변수를 설정해도 되며 환경변수가 우선합니다. `GEMINI_MODEL`은 선택 항목입니다.

**보안 조치:** 이전 `test.py`에 Gemini 키가 직접 들어 있었습니다. 파일에서 키를 제거해도 과거 Git 이력의 키는 유효할 수 있으므로 해당 키를 폐기하고 새 키를 발급해야 합니다. 실제 키를 코드·이슈·PR에 적지 마세요.

## 동작

- 날짜 기본값은 한국 시간입니다. 미래 날짜는 선택하지 못합니다.
- DART `total_page`까지 조회하고 접수번호 중복을 제거합니다.
- 공시가 없는 날(`013`)은 빈 목록입니다. 조회 실패는 오류를 표시하며 가짜 공시로 대체하지 않습니다.
- 시연 데이터는 `backend/dart_client.py`의 `USE_SAMPLE_DATA = True`에서만 사용합니다. 화면에 샘플 표시를 하고 가짜 접수번호의 원문 링크는 숨깁니다.
- AI는 20건씩 분류하고 응답 스키마·접수번호 일치·요약 길이를 검증합니다. 키가 없거나 응답을 검증할 수 없으면 **미분류**로 표시합니다. 오류 원문에 포함될 수 있는 키나 요청 URL은 화면에 표시하지 않습니다.
- 조회 결과는 10분 캐시되며, 필터·정렬 변경 후에도 현재 세션에 남습니다. **최신화**는 선택 날짜의 캐시만 지우고 즉시 다시 조회합니다. AI 실패 결과는 다음 조회에서 재시도합니다.
- 중요 공시 팝업과 알림 자동 저장은 **시연 버튼 전용**입니다. 일반 공시 조회는 알림을 자동 저장하지 않는 기존 정책을 유지합니다.
- 보관함은 현재 접속 세션에서만 유지됩니다. 데이터베이스 저장·백그라운드 자동 수집·푸시 알림 기능은 구현되어 있지 않습니다.
- 영향도는 제목 기준 AI 분류이며 주가 예측이나 투자 권유가 아닙니다.

## 검사

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

테스트는 외부 API·실제 키 없이 응답을 모의합니다. DART 페이지 조회·무공시·오류, AI 실패·잘못된 응답, 화면 필터 유지·최신화·보관함 이동을 검증합니다. GitHub Actions는 Python 3.11/3.12에서 같은 검사를 실행합니다.

실제 연동은 새 키를 설정한 뒤 `python test_backend.py`로 별도 확인합니다. `python test.py`는 Gemini 연결만 확인합니다. 두 파일은 직접 실행할 때만 외부 API를 호출하며 호출 한도 또는 비용이 발생할 수 있습니다.

## 변경 기록

- 기존 v2: Gemini 전환, 중요도 배지, 시연용 High 팝업 (`readme.txt`).
- 2026-10-13 검사·수정: 키 하드코딩 제거, DART 전 페이지 조회·실패 처리, AI 응답 검증·미분류 처리, 화면 재실행·최신화 보완, 오프라인 회귀 검사와 CI 추가.
