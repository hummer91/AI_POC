# AI Chatbot POC 구현 계획 V2

> 건강기능식품 OEM 자동 견적 시스템

## 🎯 목표

저비용 LLM + 검색 API + 원료 DB를 활용하여, 건강기능식품 OEM 자동 견적 챗봇 구현

**핵심 기능:**
1. 사용자 요청 파싱 (원료, 제형, 수량)
2. 원료 DB에서 가격 조회
3. 레퍼런스 제품 검색 (시중 배합비 참조)
4. 견적 자동 계산
5. MOQ 규칙 적용

---

## 📦 기술 스택

### LLM API (4개)
| 모델 | Input/Output ($/1M) | 용도 |
|------|---------------------|------|
| **Gemini 2.0 Flash** | $0.10 / $0.40 | 기본 |
| **GPT-5-nano** | $0.05 / $0.40 | 최저가 테스트 |
| **GPT-5-mini** | $0.25 / $2.00 | 품질 비교 |
| **GPT-4o-mini** | $0.15 / $0.60 | 안정성 비교 |

### 검색 API (4개)
| API | 무료 한도 | 용도 |
|-----|----------|------|
| DDGS | 무제한* | 레퍼런스 제품 검색 |
| Brave | 2,000/월 | Fallback |
| Tavily | 1,000/월 | AI 특화 검색 |
| Google CSE | 100/일 | 정확한 검색 |

### 데이터
| 데이터 | 형식 | 내용 |
|--------|------|------|
| 원료 DB | JSON | 원료 가격, 부형제 가격 |
| 임가공비 | JSON | 제환비, 포장비 등 |
| MOQ 규칙 | JSON | 최소 주문 수량 |
| 레퍼런스 | JSON | 시중 제품 배합비 |

---

## 🏗️ 프로젝트 구조

```
99_ai_POC/
├── app/
│   ├── main.py                 # Streamlit 메인 앱
│   ├── config.py               # 설정
│   ├── providers/
│   │   ├── search.py           # 검색 API (4개)
│   │   └── llm.py              # LLM API (4개)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ingredient.py       # 원료 DB 조회
│   │   ├── calculator.py       # 견적 계산
│   │   └── reference.py        # 레퍼런스 제품 검색
│   └── utils/
│       └── prompt.py           # 프롬프트 템플릿
├── data/
│   └── ingredient_db.json      # 원료/임가공/MOQ 데이터
├── docs/
│   ├── API_KEY_SETUP_GUIDE.md
│   ├── POC_PLAN.md
│   └── POC_PLAN_V2.md          # 변경된 플랜
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🔧 구현 단계

### Phase 1: 기반 설정 ✅ (완료)
- [x] 프로젝트 폴더 구조 생성
- [x] requirements.txt 작성
- [x] .env.example 작성
- [x] .gitignore 설정
- [x] API 키 발급 가이드 문서

### Phase 2: 검색/LLM Provider ✅ (완료)
- [x] 검색 Provider 4개 구현 (DDGS, Brave, Tavily, Google)
- [x] LLM Provider 4개 구현 (Gemini, GPT-5-nano/mini, GPT-4o-mini)
- [x] Fallback 로직 구현

### Phase 3: 원료 DB 서비스 ✅ (완료)
- [x] 원료 DB JSON 생성
- [x] 원료 조회 서비스 (ingredient.py)
- [x] 가격 조회 함수
- [x] 부형제 자동 추천 함수

### Phase 4: 견적 계산 서비스 ✅ (완료)
- [x] 견적 계산기 (calculator.py)
- [x] 원료비 계산
- [x] 부재료비 계산 (포장재)
- [x] 임가공비 계산
- [x] MOQ 규칙 적용
- [x] 총 견적 산출

### Phase 5: 레퍼런스 검색 서비스 ✅ (완료)
- [x] 레퍼런스 검색 (reference.py)
- [x] 시중 제품 검색 (검색 API 활용)
- [x] 배합비 추출/제안

### Phase 6: 프롬프트 설계 ✅ (완료)
- [x] 시스템 프롬프트 (견적 서비스용)
- [x] 대화 흐름 설계
  - 제형 선택 → 포장 선택 → 원료 비율 → 수량 → 견적
- [x] 견적 출력 포맷 템플릿

### Phase 7: Streamlit UI ✅ (완료)
- [x] 메인 레이아웃 수정
- [x] 견적 요청 폼
- [x] 견적 결과 표시
- [x] 비용 상세 내역 표시

### Phase 8: 테스트 및 문서화 ✅ (완료)
- [x] 테스트 시나리오 실행 (7개 테스트 모두 통과)
- [x] README.md 업데이트
- [x] 결과 비교 문서

---

## 💬 대화 흐름 설계

```
사용자: 차전자피 환을 만들고 싶어. 5g씩 30포가 1박스고, 총 3000박스 제작할 예정이야
        ↓
시스템: [제품 정보 파싱]
        - 원료: 차전자피
        - 제형: 환
        - 1포: 5g
        - 1박스: 30포
        - 수량: 3000박스
        ↓
시스템: 원료의 비율을 알려주세요.
        레퍼런스 제품(종근당건강 차전자피 환): 차전자피 95%, 결정셀룰로스 5%
        비율을 잘 모르시면 레퍼런스 제품의 비율을 적용할까요?
        ↓
사용자: 차전자피 80%, 부원료는 알아서 해줘
        ↓
시스템: [원료 DB 조회 + 견적 계산]
        ↓
시스템: [[OEM 환 제품 예상견적]
        ▶ 제품정보
        주원료: 차전자피 80% (360.0kg)
        부원료: 결정셀룰로스 10%, 정제포도당 8%, 이산화규소 1%, 스테아린산마그네슘 1%
        ...
        총 예상금액: 약 19,566,300원 (VAT 별도)]
```

---

## 📊 견적 계산 로직

### 1. 총 원료량 계산
```python
total_kg = gram_per_pouch * pouch_per_box * boxes / 1000
# 예: 5g × 30포 × 3000박스 / 1000 = 450kg
```

### 2. 원료비 계산
```python
ingredient_cost = Σ(total_kg × ratio × price_per_kg)
# 예: 450kg × 80% × 8,500원 = 3,060,000원 (차전자피)
```

### 3. 부재료비 계산
```python
packaging_cost = (pouch_count × 스틱포장비) + (box_count × 단박스비)
# 예: 90,000포 × 35원 + 3,000박스 × 400원 = 4,350,000원
```

### 4. 임가공비 계산
```python
processing_cost = total_kg × 제환비
# 예: 450kg × 11,000원 = 4,950,000원
```

### 5. MOQ 적용
```python
if boxes < MOQ:
    boxes = MOQ  # 2000 또는 3000
```

### 6. 총 견적
```python
total = ingredient_cost + packaging_cost + processing_cost
price_per_box = total / boxes
```

---

## 🎯 품질 비교 포인트

| 항목 | GPT-5-mini | GPT-4o | 우리 POC |
|------|------------|--------|----------|
| 부원료 일관성 | ✅ 일관 | ❌ 매번 다름 | ✅ DB 기반 |
| 계산 정확도 | ✅ 정확 | ⚠️ 오차 | ✅ 로직 고정 |
| 레퍼런스 제품 | ✅ 일관 | ❌ 랜덤 | ✅ DB + 검색 |
| 비용 | 높음 | 높음 | ✅ 저비용 |

---

## ✅ 완료 조건

1. 사용자가 제품 정보 입력 → 자동 견적 출력
2. 4개 LLM 비교 테스트 가능
3. 원료 DB 기반 일관된 가격 산출
4. MOQ 규칙 자동 적용
5. 레퍼런스 제품 검색 및 배합비 제안

---

## 💰 예상 비용 (일 100건 견적 기준)

| LLM | 월 비용 |
|-----|--------|
| GPT-5-nano | ~$0.50 |
| Gemini 2.0 Flash | ~$0.50 |
| GPT-4o-mini | ~$0.80 |
| GPT-5-mini | ~$2.20 |

> 검색 API: 무료 티어 조합으로 **$0**

---

**예상 추가 소요 시간: 약 60분**

- Phase 3 (원료 DB 서비스): 15분
- Phase 4 (견적 계산): 20분
- Phase 5 (레퍼런스 검색): 10분
- Phase 6 (프롬프트 수정): 10분
- Phase 7 (UI 수정): 5분

---

*최종 업데이트: 2025-12-04*
