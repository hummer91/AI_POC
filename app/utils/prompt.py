"""
프롬프트 템플릿 모듈
- 시스템 프롬프트
- 검색 결과 컨텍스트 포맷
- 답변 생성 프롬프트
"""

from typing import Optional
from app.providers.search import SearchResult


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
