# AI POC - 건강기능식품 검색 챗봇

검색 API + LLM 조합 테스트를 위한 POC 프로젝트

## 목표

저비용 LLM + 무료 검색 API 조합이 ChatGPT 사이트 수준의 답변 품질을 낼 수 있는지 검증

## 기술 스택

### 검색 API (4개)
| API | 무료 한도 | 특징 |
|-----|----------|------|
| DDGS | 무제한* | DuckDuckGo 기반 |
| Brave | 2,000/월 | 독립 인덱스 |
| Tavily | 1,000/월 | AI/RAG 특화 |
| Google CSE | 100/일 | 가장 정확 |

### LLM API (4개)
| 모델 | Input/Output ($/1M) | 특징 |
|------|---------------------|------|
| Gemini 2.0 Flash | $0.10 / $0.40 | Google, 빠름 |
| GPT-5-nano | $0.05 / $0.40 | 최저가 |
| GPT-5-mini | $0.25 / $2.00 | GPT-5 80% 성능 |
| GPT-4o-mini | $0.15 / $0.60 | 검증됨 |

## 설치

```bash
# 저장소 클론
git clone https://github.com/hummer91/AI_POC.git
cd AI_POC

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에 API 키 입력
```

## 실행

```bash
streamlit run app/main.py
```

브라우저에서 http://localhost:8501 접속

## 프로젝트 구조

```
99_ai_POC/
├── app/
│   ├── main.py              # Streamlit 메인 앱
│   ├── config.py            # 설정
│   ├── providers/
│   │   ├── search.py        # 검색 API (4개)
│   │   └── llm.py           # LLM API (4개)
│   └── utils/
│       └── prompt.py        # 프롬프트 템플릿
├── docs/
│   ├── API_KEY_SETUP_GUIDE.md   # API 키 발급 가이드
│   ├── LLM_API_COST_COMPARISON.md
│   └── POC_PLAN.md
├── .env.example
├── requirements.txt
└── README.md
```

## API 키 설정

자세한 발급 방법은 [API_KEY_SETUP_GUIDE.md](docs/API_KEY_SETUP_GUIDE.md) 참고

```bash
# .env 필수 항목
OPENAI_API_KEY=sk-...        # GPT 모델용
GOOGLE_API_KEY=AIza...       # Gemini용

# 선택 항목 (검색 API)
BRAVE_API_KEY=BSA...         # Brave Search
TAVILY_API_KEY=tvly-...      # Tavily
GOOGLE_CSE_API_KEY=AIza...   # Google CSE
GOOGLE_CSE_ID=...            # Google CSE
```

## 기능

- 4개 검색 API × 4개 LLM = **16가지 조합** 테스트
- Fallback 로직: 검색 실패 시 자동으로 다른 API 시도
- 메트릭 표시: 응답 시간, 토큰 수, 예상 비용
- 토큰 절약 모드: 프롬프트 압축으로 비용 절감

## 예상 비용

일 1,000건 질문 기준 (검색 무료 티어 사용 시)

| LLM | 월 비용 |
|-----|--------|
| GPT-5-nano | ~$4.35 |
| Gemini 2.0 Flash | ~$5.10 |
| GPT-4o-mini | ~$7.65 |
| GPT-5-mini | ~$21.75 |

## License

MIT
