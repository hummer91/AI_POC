"""
프롬프트 템플릿 모듈
- 시스템 프롬프트
- 검색 결과 컨텍스트 포맷
- 답변 생성 프롬프트
- OEM 견적 서비스 프롬프트
"""

from typing import Optional
from app.providers.search import SearchResult


# ========================================
# OEM 견적 서비스용 프롬프트
# ========================================

QUOTE_SYSTEM_PROMPT = """당신은 건강기능식품 OEM 견적 전문 AI 어시스턴트입니다.

## 역할
- 사용자의 제품 요청에서 필요한 정보를 추출합니다
- 원료 비율, 제형, 수량 등을 파악합니다
- 레퍼런스 제품을 안내하고 배합비를 제안합니다
- 최종 견적을 계산하여 제공합니다

## 대화 흐름
1. **제품 정보 파악**: 원료, 제형, 포장 규격, 수량 확인
2. **원료 비율 확인**: 주원료/부원료 비율 확인 또는 레퍼런스 제안
3. **견적 제공**: 원료비, 포장비, 임가공비 포함 총 견적 제공

## 정보 추출 포맷 (JSON)
사용자 메시지에서 다음 정보를 추출하세요:
```json
{
  "ingredient": "주원료명",
  "product_type": "환/분말/정제/과립",
  "gram_per_pouch": 1포당 그램수,
  "pouch_per_box": 1박스당 포수,
  "boxes": 총 박스수,
  "ratios": {"원료명": 비율, ...} 또는 null
}
```

## 응답 원칙
1. 누락된 정보가 있으면 친절하게 질문합니다
2. 레퍼런스 제품 정보를 제공할 때는 출처를 명시합니다
3. 견적은 항상 상세 내역과 함께 제공합니다
4. MOQ(최소주문수량) 미달 시 자동 조정을 안내합니다

## 제형별 기본 정보
- 환: 분말을 환 형태로 성형, 제환비 11,000원/kg
- 분말: 스틱 포장, 분말충진비 8,000원/kg
- 정제: 타정, 정제비 15,000원/kg
- 과립: 과립 성형, 과립비 12,000원/kg

## MOQ 기준
- 최소 박스 수: 2,000박스
- 최소 생산량: 300kg
"""

QUOTE_SYSTEM_PROMPT_COMPACT = """건강기능식품 OEM 견적 AI입니다.

역할: 제품 정보 추출 → 원료 비율 확인 → 견적 계산

추출 정보: 원료, 제형(환/분말/정제/과립), 규격(g×포×박스), 비율
MOQ: 2000박스 또는 300kg 이상

누락 정보는 질문, 레퍼런스 제품 제안, 상세 견적 제공"""


# 정보 추출 프롬프트
EXTRACT_PRODUCT_INFO_PROMPT = """다음 사용자 메시지에서 OEM 제품 정보를 추출하세요.

사용자 메시지: {user_message}

다음 JSON 형식으로 응답하세요 (코드블록 없이 JSON만):
{{
  "ingredient": "주원료명 (예: 차전자피)",
  "product_type": "제형 (환/분말/정제/과립 중 하나, 없으면 null)",
  "gram_per_pouch": 1포당 그램수 (숫자, 없으면 null),
  "pouch_per_box": 1박스당 포수 (숫자, 없으면 null),
  "boxes": 총 박스수 (숫자, 없으면 null),
  "ratios": {{"원료명": 비율}} 또는 null (비율 모르면 null)
}}

예시:
- "차전자피 환 5g 30포 3000박스" → {{"ingredient": "차전자피", "product_type": "환", "gram_per_pouch": 5, "pouch_per_box": 30, "boxes": 3000, "ratios": null}}
- "차전자피 80% 나머지는 알아서" → {{"ingredient": "차전자피", "product_type": null, "gram_per_pouch": null, "pouch_per_box": null, "boxes": null, "ratios": {{"차전자피": 80}}}}"""


# 견적 결과 템플릿
QUOTE_RESULT_TEMPLATE = """【OEM {product_type} 제품 예상 견적】

▶ 제품정보
   주원료: {main_ingredient} {main_ratio}% ({main_kg}kg)
   부원료: {sub_ingredients}
   제형: {product_type}
   규격: {gram_per_pouch}g × {pouch_per_box}포/박스
   수량: {boxes:,}박스 ({total_pouches:,}포)

▶ 비용 상세
   1. 원료비: {ingredient_cost:,}원
{ingredient_details}
   2. 포장비: {packaging_cost:,}원
      - 스틱포장: {pouch_count:,}포 × {stick_price}원 = {stick_cost:,}원
      - 단박스: {box_count:,}개 × {box_price}원 = {box_cost:,}원
   3. 임가공비: {processing_cost:,}원
      - {process_type}비: {total_kg}kg × {process_price:,}원

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 총 예상금액: {total_cost:,}원 (VAT 별도)
   박스당 단가: {price_per_box:,}원
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{warnings}"""


# 누락 정보 질문 템플릿
MISSING_INFO_QUESTIONS = {
    "ingredient": "어떤 원료로 제품을 만드시겠어요? (예: 차전자피, 비타민C 등)",
    "product_type": "어떤 제형으로 제작할까요? (환 / 분말 / 정제 / 과립)",
    "gram_per_pouch": "1포당 몇 그램으로 할까요? (일반적으로 3~5g)",
    "pouch_per_box": "1박스에 몇 포를 담을까요? (일반적으로 30포)",
    "boxes": "총 몇 박스를 생산할 예정인가요? (최소 2,000박스)",
    "ratios": "원료 비율을 알려주세요. 잘 모르시면 레퍼런스 제품 비율을 추천해드릴까요?",
}


# 레퍼런스 제안 템플릿
REFERENCE_SUGGESTION_TEMPLATE = """원료의 비율을 알려주세요.

📌 레퍼런스 제품 참고:
{reference_products}

비율을 잘 모르시면 레퍼런스 제품의 비율을 적용할까요?
(예: "레퍼런스대로 해주세요" 또는 "차전자피 80%, 나머지는 알아서")"""


# ========================================
# 기존 검색 기반 프롬프트
# ========================================

# 시스템 프롬프트 (건강기능식품 도메인)
SYSTEM_PROMPT = """당신은 건강기능식품 전문 AI 어시스턴트입니다.

## 역할
- 건강기능식품 원료, 성분, 효능에 대한 정확한 정보 제공
- 사용자의 질문에 검색 결과를 바탕으로 신뢰할 수 있는 답변 작성
- 과학적 근거가 있는 정보만 제공

## 답변 원칙
1. **정확성**: 검색 결과에 기반하여 답변하세요
2. **출처 명시**: 정보의 출처를 명확히 밝히세요
3. **객관성**: 과장 없이 객관적으로 설명하세요
4. **안전성**: 의학적 조언은 하지 마세요. 전문가 상담을 권장하세요
5. **간결성**: 핵심 정보를 명확하게 전달하세요

## 주의사항
- 검색 결과에 없는 내용은 추측하지 마세요
- "~할 수 있습니다", "~에 도움이 될 수 있습니다" 등 조심스러운 표현 사용
- 건강 상태에 대한 진단이나 처방은 절대 하지 마세요
"""


# 간소화된 시스템 프롬프트 (토큰 절약용)
SYSTEM_PROMPT_COMPACT = """건강기능식품 전문 AI입니다.
- 검색 결과 기반으로 답변
- 출처 명시, 과장 금지
- 의학적 조언 불가, 전문가 상담 권장"""


def format_search_context(results: list[SearchResult]) -> str:
    """
    검색 결과를 LLM 컨텍스트 형식으로 변환

    Args:
        results: 검색 결과 리스트

    Returns:
        포맷된 컨텍스트 문자열
    """
    if not results:
        return "검색 결과가 없습니다."

    context_parts = ["## 검색 결과\n"]

    for i, r in enumerate(results, 1):
        context_parts.append(f"""### [{i}] {r.title}
- URL: {r.url}
- 내용: {r.snippet}
""")

    return "\n".join(context_parts)


def format_search_context_compact(results: list[SearchResult]) -> str:
    """
    검색 결과를 압축된 형식으로 변환 (토큰 절약)

    Args:
        results: 검색 결과 리스트

    Returns:
        압축된 컨텍스트 문자열
    """
    if not results:
        return "[검색 결과 없음]"

    lines = []
    for i, r in enumerate(results, 1):
        # 스니펫을 200자로 제한
        snippet = r.snippet[:200] + "..." if len(r.snippet) > 200 else r.snippet
        lines.append(f"[{i}] {r.title}: {snippet}")

    return "\n".join(lines)


def build_user_prompt(
    query: str,
    search_results: list[SearchResult],
    compact: bool = False
) -> str:
    """
    사용자 질문 + 검색 결과를 결합한 프롬프트 생성

    Args:
        query: 사용자 질문
        search_results: 검색 결과 리스트
        compact: 압축 모드 사용 여부

    Returns:
        완성된 사용자 프롬프트
    """
    if compact:
        context = format_search_context_compact(search_results)
    else:
        context = format_search_context(search_results)

    return f"""{context}

---

## 질문
{query}

위 검색 결과를 참고하여 질문에 답변해주세요. 답변 시 출처를 명시해주세요."""


def build_user_prompt_simple(query: str) -> str:
    """
    검색 없이 단순 질문 프롬프트 생성 (비교용)

    Args:
        query: 사용자 질문

    Returns:
        단순 프롬프트
    """
    return f"""## 질문
{query}

위 질문에 대해 알고 있는 정보를 바탕으로 답변해주세요."""


def get_system_prompt(compact: bool = False) -> str:
    """시스템 프롬프트 반환"""
    return SYSTEM_PROMPT_COMPACT if compact else SYSTEM_PROMPT


# 토큰 수 추정 함수 (간단한 방식)
def estimate_tokens(text: str) -> int:
    """
    텍스트의 토큰 수 추정 (한국어/영어 혼합)

    대략적인 추정:
    - 영어: 단어당 ~1.3 토큰
    - 한국어: 글자당 ~0.5 토큰
    """
    # 간단하게 문자 수 기반으로 추정
    return int(len(text) * 0.4)  # 한국어 기준 대략적 추정


# ========================================
# OEM 견적 헬퍼 함수
# ========================================

def get_quote_system_prompt(compact: bool = False) -> str:
    """OEM 견적용 시스템 프롬프트 반환"""
    return QUOTE_SYSTEM_PROMPT_COMPACT if compact else QUOTE_SYSTEM_PROMPT


def build_extract_prompt(user_message: str) -> str:
    """정보 추출용 프롬프트 생성"""
    return EXTRACT_PRODUCT_INFO_PROMPT.format(user_message=user_message)


def build_missing_info_question(missing_fields: list[str]) -> str:
    """
    누락 정보에 대한 질문 생성

    Args:
        missing_fields: 누락된 필드 목록

    Returns:
        질문 문자열
    """
    questions = []
    for field in missing_fields:
        if field in MISSING_INFO_QUESTIONS:
            questions.append(MISSING_INFO_QUESTIONS[field])

    if not questions:
        return ""

    return "추가 정보가 필요합니다:\n\n" + "\n".join(f"❓ {q}" for q in questions)


def build_reference_suggestion(
    ingredient_name: str,
    references: list[dict]
) -> str:
    """
    레퍼런스 제품 제안 메시지 생성

    Args:
        ingredient_name: 주원료명
        references: 레퍼런스 제품 리스트 [{"name": ..., "ratio": {...}}, ...]

    Returns:
        레퍼런스 제안 메시지
    """
    if not references:
        return f"{ingredient_name}에 대한 레퍼런스 제품이 없습니다. 원하시는 비율을 직접 알려주세요."

    ref_lines = []
    for i, ref in enumerate(references, 1):
        ratio_str = ", ".join(f"{k} {v}%" for k, v in ref.get("ratio", {}).items())
        ref_lines.append(f"   {i}. {ref['name']}: {ratio_str}")

    reference_products = "\n".join(ref_lines)

    return REFERENCE_SUGGESTION_TEMPLATE.format(reference_products=reference_products)


def get_conversation_state_prompt(state: dict) -> str:
    """
    대화 상태에 따른 시스템 프롬프트 추가 지시사항 생성

    Args:
        state: 현재 대화 상태 (수집된 정보)

    Returns:
        추가 지시사항 문자열
    """
    collected = []
    missing = []

    fields = {
        "ingredient": "주원료",
        "product_type": "제형",
        "gram_per_pouch": "1포당 그램",
        "pouch_per_box": "1박스당 포수",
        "boxes": "박스 수",
        "ratios": "원료 비율"
    }

    for field, label in fields.items():
        if state.get(field):
            collected.append(f"- {label}: {state[field]}")
        else:
            missing.append(label)

    prompt_parts = []

    if collected:
        prompt_parts.append("## 수집된 정보\n" + "\n".join(collected))

    if missing:
        prompt_parts.append("## 아직 필요한 정보\n" + ", ".join(missing))

    return "\n\n".join(prompt_parts)
