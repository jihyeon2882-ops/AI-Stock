from google import genai

# 새로 발급받은 API 키를 따옴표 안에 넣어주세요!
API_KEY = "AIzaSyB_HkhlfZWeuGrYmLe0vN9u90-Oi-_byow" 

client = genai.Client(api_key=API_KEY)

# 최신 구글 모델 3대장 테스트
models_to_test = [
    "gemini-2.5-flash",       # 현재 구글의 주력 표준 모델
    "gemini-2.5-flash-lite",  # 가볍고 빠른 무료 최적화 모델
    "gemini-2.0-flash"        # 이전 버전
]

for model_name in models_to_test:
    try:
        print(f"\n🚀 [{model_name}] 모델 테스트 중...")
        response = client.models.generate_content(
            model=model_name,
            contents="안녕? 공시 요약 테스트야. 대답해줘."
        )
        print(f"✅ 대성공!! 이 모델을 쓰시면 됩니다. (응답: {response.text.strip()})")
    except Exception as e:
        print(f"❌ 실패 (원인: {e})")