# API Key 발급 가이드

> AI POC 프로젝트에 필요한 모든 API 키 발급 방법

## 목차

1. [OpenAI API (GPT-5, GPT-4o)](#1-openai-api)
2. [Google AI API (Gemini)](#2-google-ai-api)
3. [Brave Search API](#3-brave-search-api)
4. [Tavily API](#4-tavily-api)
5. [Google Custom Search API](#5-google-custom-search-api)
6. [DDGS (DuckDuckGo)](#6-ddgs-duckduckgo)

---

## 1. OpenAI API

> GPT-5-nano, GPT-5-mini, GPT-4o-mini 사용

### 비용
| 모델 | Input | Output | 캐시 할인 |
|------|-------|--------|----------|
| GPT-5-nano | $0.05/1M | $0.40/1M | 90% |
| GPT-5-mini | $0.25/1M | $2.00/1M | 90% |
| GPT-4o-mini | $0.15/1M | $0.60/1M | 50% |

### 발급 방법

1. **OpenAI 계정 생성**
   - https://platform.openai.com/ 접속
   - "Sign up" 클릭 → 이메일 또는 Google/Microsoft 계정으로 가입

2. **결제 정보 등록** (필수)
   - 좌측 메뉴 → "Settings" → "Billing"
   - "Add payment method" 클릭
   - 신용카드 정보 입력
   - 💡 **팁**: 최소 $5부터 충전 가능

3. **API 키 생성**
   - 좌측 메뉴 → "API keys"
   - "Create new secret key" 클릭
   - 이름 입력 (예: "AI_POC")
   - 키 복사 후 안전하게 보관

   ```
   sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

4. **사용량 제한 설정** (권장)
   - "Settings" → "Limits"
   - Monthly budget 설정 (예: $10)
   - 예상치 못한 과금 방지

### 주의사항
- ⚠️ API 키는 한 번만 표시됨 - 반드시 복사해서 저장
- ⚠️ 키를 GitHub 등에 노출하지 않도록 주의
- ⚠️ 신규 계정은 Rate Limit이 낮을 수 있음

---

## 2. Google AI API

> Gemini 2.0 Flash 사용

### 비용
| 모델 | Input | Output |
|------|-------|--------|
| Gemini 2.0 Flash | $0.10/1M | $0.40/1M |

💡 **무료 티어**: 분당 15회, 일 1,500회 무료

### 발급 방법

1. **Google AI Studio 접속**
   - https://aistudio.google.com/ 접속
   - Google 계정으로 로그인

2. **API 키 생성**
   - 좌측 메뉴 → "Get API key"
   - "Create API key" 클릭
   - 프로젝트 선택 또는 새 프로젝트 생성
   - 키 복사

   ```
   AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

3. **테스트**
   ```bash
   curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
   ```

### 주의사항
- ⚠️ 무료 티어는 Rate Limit 있음 (분당 15회)
- ⚠️ 프로덕션 사용 시 유료 전환 필요

---

## 3. Brave Search API

> 독립적인 검색 인덱스, 프라이버시 중심

### 비용
- **무료**: 2,000회/월
- **유료**: $3/1,000회

### 발급 방법

1. **Brave Search API 페이지 접속**
   - https://brave.com/search/api/ 접속
   - "Get Started" 클릭

2. **계정 생성**
   - 이메일로 가입 또는 GitHub 계정 연동
   - 이메일 인증 완료

3. **API 키 생성**
   - Dashboard 접속
   - "API Keys" 탭
   - "Create API Key" 클릭
   - 용도 선택: "Web Search"
   - 키 복사

   ```
   BSAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

4. **테스트**
   ```bash
   curl -H "X-Subscription-Token: YOUR_API_KEY" \
     "https://api.search.brave.com/res/v1/web/search?q=test"
   ```

### 주의사항
- ⚠️ 무료 티어는 월 2,000회 제한
- ⚠️ 초과 시 자동으로 유료 전환되지 않음 (안전)

---

## 4. Tavily API

> AI/RAG에 최적화된 검색 API

### 비용
- **무료**: 1,000회/월
- **유료**: $0.008/회 (~$8/1,000회)

### 발급 방법

1. **Tavily 웹사이트 접속**
   - https://tavily.com/ 접속
   - "Get API Key" 또는 "Sign Up" 클릭

2. **계정 생성**
   - 이메일로 가입
   - 이메일 인증 완료

3. **API 키 확인**
   - 로그인 후 Dashboard
   - API Key가 자동 생성되어 있음
   - 키 복사

   ```
   tvly-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

4. **테스트**
   ```bash
   curl -X POST "https://api.tavily.com/search" \
     -H "Content-Type: application/json" \
     -d '{"api_key": "YOUR_API_KEY", "query": "test"}'
   ```

### 특징
- ✅ AI 검색에 최적화된 응답 포맷
- ✅ 자동 요약 기능 포함
- ✅ LLM 컨텍스트에 바로 사용 가능

---

## 5. Google Custom Search API

> Google 검색 결과를 API로 제공

### 비용
- **무료**: 100회/일
- **유료**: $5/1,000회

### 발급 방법 (2단계 필요)

### Step 1: API 키 생성

1. **Google Cloud Console 접속**
   - https://console.cloud.google.com/ 접속
   - Google 계정으로 로그인

2. **프로젝트 생성**
   - 상단 프로젝트 선택 드롭다운 클릭
   - "새 프로젝트" 클릭
   - 이름 입력 (예: "AI-POC")
   - "만들기" 클릭

3. **Custom Search API 활성화**
   - 좌측 메뉴 → "API 및 서비스" → "라이브러리"
   - "Custom Search API" 검색
   - "사용" 클릭

4. **API 키 생성**
   - 좌측 메뉴 → "API 및 서비스" → "사용자 인증 정보"
   - "사용자 인증 정보 만들기" → "API 키"
   - 키 복사

   ```
   AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### Step 2: 검색 엔진 ID (CSE ID) 생성

1. **Programmable Search Engine 접속**
   - https://programmablesearchengine.google.com/ 접속
   - "시작하기" 또는 "Add" 클릭

2. **검색 엔진 설정**
   - 검색 엔진 이름 입력 (예: "AI POC Search")
   - "전체 웹 검색" 선택
   - "만들기" 클릭

3. **검색 엔진 ID 복사**
   - 생성 완료 후 "제어판" 클릭
   - "기본사항" 탭에서 "검색 엔진 ID" 복사

   ```
   xxxxxxxxxxxxxxxxx
   ```

4. **테스트**
   ```bash
   curl "https://www.googleapis.com/customsearch/v1?key=YOUR_API_KEY&cx=YOUR_CSE_ID&q=test"
   ```

### 주의사항
- ⚠️ 무료는 일 100회로 매우 제한적
- ⚠️ API 키와 CSE ID 두 개 모두 필요
- ⚠️ 결제 정보 등록 없이도 무료 티어 사용 가능

---

## 6. DDGS (DuckDuckGo)

> API 키 불필요, 완전 무료

### 비용
- **무료**: 무제한 (Rate Limit 있음)

### 사용 방법

API 키가 필요 없음. Python 라이브러리 설치만 하면 됨:

```bash
pip install duckduckgo_search
```

### 사용 예시

```python
from duckduckgo_search import DDGS

with DDGS() as ddgs:
    results = ddgs.text("비타민C 효능", max_results=5)
    for r in results:
        print(r['title'], r['href'])
```

### 주의사항
- ⚠️ 너무 빈번한 요청 시 일시적 차단 가능
- ⚠️ 공식 API가 아닌 스크래핑 방식
- ⚠️ 상업적 대규모 사용은 권장하지 않음

---

## 빠른 설정 체크리스트

```bash
# 1. .env 파일 생성
cp .env.example .env

# 2. 필수 API 키 입력 (최소 구성)
OPENAI_API_KEY=sk-...      # 또는 GOOGLE_API_KEY (둘 중 하나)

# 3. 검색 API (선택, DDGS는 키 불필요)
BRAVE_API_KEY=BSA...       # 2,000회/월 무료
TAVILY_API_KEY=tvly-...    # 1,000회/월 무료

# 4. 테스트 실행
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('OK' if os.getenv('OPENAI_API_KEY') else 'MISSING')"
```

## 권장 설정 순서

1. **DDGS** - 키 불필요, 바로 사용 가능
2. **Google AI (Gemini)** - 무료 티어 넉넉, 발급 쉬움
3. **Brave Search** - 무료 2,000회, 발급 쉬움
4. **OpenAI** - 결제 정보 필요하지만 가장 안정적
5. **Tavily** - AI 특화, 무료 1,000회
6. **Google CSE** - 설정 복잡, 무료 100회로 적음

---

## 문제 해결

### "Invalid API Key" 오류
- API 키 앞뒤 공백 확인
- .env 파일이 프로젝트 루트에 있는지 확인
- 키가 올바른 서비스용인지 확인

### "Rate Limit Exceeded" 오류
- 무료 티어 한도 초과
- 잠시 후 재시도 또는 다른 API로 fallback

### "Quota Exceeded" 오류
- 월간/일간 한도 초과
- 다음 달/일까지 대기 또는 유료 전환

---

*최종 업데이트: 2025-12-04*
