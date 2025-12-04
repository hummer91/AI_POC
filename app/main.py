"""
AI POC - 건강기능식품 OEM 견적 챗봇
Streamlit 메인 앱
"""

import json
import time
import streamlit as st
from dotenv import load_dotenv

# .env 로드
load_dotenv()

from app.config import (
    APP_TITLE, APP_ICON,
    DEFAULT_SEARCH_RESULTS, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE,
    LLM_PRICING, SEARCH_PRICING
)
from app.providers.search import get_search_manager, SearchResult
from app.providers.llm import get_llm_manager, LLMResponse
from app.services import (
    IngredientService,
    QuoteCalculator,
    ProductSpec,
    ReferenceService,
)
from app.utils.prompt import (
    get_system_prompt,
    get_quote_system_prompt,
    build_user_prompt,
    build_extract_prompt,
    build_reference_suggestion,
    estimate_tokens
)


# 페이지 설정
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide"
)


def init_session_state():
    """세션 상태 초기화"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "last_metrics" not in st.session_state:
        st.session_state.last_metrics = {}
    if "quote_state" not in st.session_state:
        st.session_state.quote_state = {}
    if "last_quote" not in st.session_state:
        st.session_state.last_quote = None


def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        st.header("⚙️ 설정")

        # 모드 선택
        st.subheader("📌 모드")
        mode = st.radio(
            "기능 선택",
            options=["OEM 견적", "검색 챗봇"],
            index=0,
            help="OEM 견적: 건강기능식품 견적 계산\n검색 챗봇: 일반 정보 검색"
        )

        st.divider()

        # LLM 선택
        st.subheader("🤖 LLM")
        llm_manager = get_llm_manager()
        available_llm = llm_manager.get_available_providers()

        llm_options = ["Gemini 2.0 Flash", "GPT-5-nano", "GPT-5-mini", "GPT-4o-mini"]
        llm_provider = st.selectbox(
            "LLM Provider",
            options=llm_options,
            index=0,
            help="답변 생성에 사용할 LLM 선택"
        )

        # LLM 상태 및 가격 표시
        for provider in llm_options:
            status = "✅" if provider in available_llm else "❌ (키 없음)"
            pricing = LLM_PRICING.get(provider, {})
            price_str = f"${pricing.get('input', 0)}/{pricing.get('output', 0)}"
            st.caption(f"{provider}: {status} - {price_str}/1M")

        st.divider()

        # 검색 API 선택 (검색 모드일 때만)
        if mode == "검색 챗봇":
            st.subheader("🔍 검색 API")
            search_manager = get_search_manager()
            available_search = search_manager.get_available_providers()

            search_options = ["DDGS", "Brave", "Tavily", "Google"]
            search_provider = st.selectbox(
                "검색 Provider",
                options=search_options,
                index=0,
                help="검색에 사용할 API 선택"
            )

            # 검색 API 상태 표시
            for provider in search_options:
                status = "✅" if provider in available_search else "❌ (키 없음)"
                free_limit = SEARCH_PRICING.get(provider, {}).get("free_limit", "")
                st.caption(f"{provider}: {status} - {free_limit}")

            st.divider()
        else:
            search_provider = "DDGS"

        # 고급 설정
        with st.expander("🔧 고급 설정"):
            max_results = st.slider(
                "검색 결과 수",
                min_value=1,
                max_value=10,
                value=DEFAULT_SEARCH_RESULTS
            )

            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=DEFAULT_TEMPERATURE,
                step=0.1
            )

            compact_mode = st.checkbox(
                "토큰 절약 모드",
                value=False,
                help="프롬프트 압축으로 비용 절감"
            )

            use_fallback = st.checkbox(
                "Fallback 사용",
                value=True,
                help="검색/LLM 실패 시 다른 API 시도"
            )

        st.divider()

        # 메트릭 표시
        st.subheader("📊 마지막 요청 메트릭")
        metrics = st.session_state.get("last_metrics", {})
        if metrics:
            st.metric("응답 시간", f"{metrics.get('response_time', 0):.2f}초")
            st.metric("입력 토큰", metrics.get('input_tokens', 0))
            st.metric("출력 토큰", metrics.get('output_tokens', 0))
            st.metric("예상 비용", f"${metrics.get('cost', 0):.6f}")
            st.caption(f"LLM: {metrics.get('llm_provider', '-')}")
        else:
            st.caption("아직 요청 없음")

        # 초기화 버튼
        if st.button("🗑️ 대화 초기화"):
            st.session_state.messages = []
            st.session_state.search_results = []
            st.session_state.last_metrics = {}
            st.session_state.quote_state = {}
            st.session_state.last_quote = None
            st.rerun()

        return {
            "mode": mode,
            "search_provider": search_provider,
            "llm_provider": llm_provider,
            "max_results": max_results,
            "temperature": temperature,
            "compact_mode": compact_mode,
            "use_fallback": use_fallback,
        }


def render_quick_quote_form():
    """빠른 견적 폼 렌더링"""
    st.subheader("📝 빠른 견적")

    ingredient_svc = IngredientService()

    col1, col2 = st.columns(2)

    with col1:
        # 원료 선택
        ingredients = ingredient_svc.list_all_ingredients()
        main_ingredients = [i["name"] for i in ingredients if i["category"] == "주원료"]

        ingredient = st.selectbox(
            "주원료",
            options=main_ingredients + ["기타 (직접 입력)"],
            index=0
        )

        if ingredient == "기타 (직접 입력)":
            ingredient = st.text_input("원료명 입력")

        # 제형 선택
        product_types = ingredient_svc.list_product_types()
        product_type = st.selectbox("제형", options=product_types, index=0)

        # 주원료 비율
        main_ratio = st.slider("주원료 비율 (%)", min_value=50, max_value=100, value=80)

    with col2:
        # 규격
        gram_per_pouch = st.number_input("1포당 그램 (g)", min_value=1, max_value=20, value=5)
        pouch_per_box = st.number_input("1박스당 포수", min_value=10, max_value=100, value=30)
        boxes = st.number_input("총 박스 수", min_value=100, max_value=100000, value=3000, step=100)

    # 레퍼런스 제품 표시
    if ingredient and ingredient != "기타 (직접 입력)":
        ref_svc = ReferenceService(ingredient_svc)
        refs = ref_svc.get_db_references(ingredient)

        if refs:
            with st.expander("📌 레퍼런스 제품 참고"):
                for ref in refs:
                    ratio_str = ", ".join(f"{k} {v}%" for k, v in ref.ratio.items())
                    st.caption(f"**{ref.name}**: {ratio_str}")

    # 견적 계산 버튼
    if st.button("💰 견적 계산", type="primary", use_container_width=True):
        if not ingredient or ingredient == "기타 (직접 입력)":
            st.error("원료를 선택하거나 입력해주세요.")
            return

        # 부형제 자동 추천
        excipients = ingredient_svc.recommend_excipients(main_ratio)
        ratios = {ingredient: main_ratio, **excipients}

        # 견적 계산
        spec = ProductSpec(
            product_type=product_type,
            gram_per_pouch=gram_per_pouch,
            pouch_per_box=pouch_per_box,
            boxes=boxes,
            ingredient_ratios=ratios
        )

        calc = QuoteCalculator(ingredient_svc)
        result = calc.calculate(spec)

        # 결과 저장 및 표시
        st.session_state.last_quote = result
        return result

    return None


def render_quote_result(result):
    """견적 결과 렌더링"""
    if not result:
        return

    st.success("견적이 계산되었습니다!")

    # 메인 요약
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 예상금액", f"{result.total_cost:,}원")
    with col2:
        st.metric("박스당 단가", f"{result.price_per_box:,}원")
    with col3:
        st.metric("총 원료량", f"{result.product_spec.total_kg:.1f}kg")

    # 상세 내역
    with st.expander("📋 상세 견적서", expanded=True):
        calc = QuoteCalculator()
        st.text(calc.format_quote(result))

    # 경고 메시지
    if result.warnings:
        for warning in result.warnings:
            st.warning(f"⚠️ {warning}")


def render_chat_interface(settings: dict):
    """대화형 견적 인터페이스"""
    st.subheader("💬 대화형 견적")
    st.caption("자연어로 견적을 요청하세요. 예: '차전자피 환 5g 30포 3000박스 만들고 싶어'")

    # 채팅 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 입력창
    if prompt := st.chat_input("견적 요청을 입력하세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # 답변 생성
        with st.chat_message("assistant"):
            with st.spinner("견적 분석 중..."):
                answer, metrics = process_quote_query(prompt, settings)

                if answer:
                    st.markdown(answer)
                else:
                    st.error("답변 생성에 실패했습니다.")

                # 상태 저장
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.session_state.last_metrics = metrics

        st.rerun()


def process_quote_query(query: str, settings: dict) -> tuple[str, dict]:
    """
    견적 관련 질문 처리

    Returns:
        (답변, 메트릭)
    """
    start_time = time.time()

    ingredient_svc = IngredientService()
    ref_svc = ReferenceService(ingredient_svc)
    calc = QuoteCalculator(ingredient_svc)
    llm_manager = get_llm_manager()

    # 1. LLM으로 정보 추출 시도
    extract_prompt = build_extract_prompt(query)
    system_prompt = get_quote_system_prompt(compact=settings["compact_mode"])

    response = llm_manager.generate(
        prompt=extract_prompt,
        provider_name=settings["llm_provider"],
        system_prompt="JSON 형식으로만 응답하세요.",
        max_tokens=500,
        temperature=0.1
    )

    # 2. 추출된 정보 파싱
    try:
        # JSON 추출 시도
        content = response.content.strip()
        # 코드 블록 제거
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        extracted = json.loads(content)
    except (json.JSONDecodeError, IndexError):
        extracted = {}

    # 3. 정보 분석 및 응답 생성
    answer_parts = []

    ingredient = extracted.get("ingredient")
    product_type = extracted.get("product_type")
    gram_per_pouch = extracted.get("gram_per_pouch")
    pouch_per_box = extracted.get("pouch_per_box")
    boxes = extracted.get("boxes")
    ratios = extracted.get("ratios")

    # 정보 확인 메시지
    if ingredient:
        answer_parts.append(f"**원료**: {ingredient}")

        # 레퍼런스 제품 조회
        refs = ref_svc.get_db_references(ingredient)
        if refs and not ratios:
            ref_list = []
            for ref in refs:
                ratio_str = ", ".join(f"{k} {v}%" for k, v in ref.ratio.items())
                ref_list.append({"name": ref.name, "ratio": ref.ratio})
            answer_parts.append("\n" + build_reference_suggestion(ingredient, ref_list))

    # 누락 정보 질문
    missing = []
    if not ingredient:
        missing.append("원료")
    if not product_type:
        missing.append("제형 (환/분말/정제/과립)")
    if not gram_per_pouch:
        missing.append("1포당 그램")
    if not pouch_per_box:
        missing.append("1박스당 포수")
    if not boxes:
        missing.append("총 박스 수")

    if missing:
        answer_parts.append(f"\n추가 정보가 필요합니다: **{', '.join(missing)}**")

    # 견적 계산 가능 여부 확인
    if all([ingredient, product_type, gram_per_pouch, pouch_per_box, boxes]):
        # 비율이 없으면 레퍼런스 또는 기본값 사용
        if not ratios:
            suggested_ratio = ref_svc.suggest_ratio(ingredient, main_ratio=80)
            ratios = suggested_ratio
            answer_parts.append(f"\n비율 미지정으로 기본값 적용: {ingredient} 80%")

        # 견적 계산
        spec = ProductSpec(
            product_type=product_type,
            gram_per_pouch=gram_per_pouch,
            pouch_per_box=pouch_per_box,
            boxes=boxes,
            ingredient_ratios=ratios
        )

        result = calc.calculate(spec)
        st.session_state.last_quote = result

        answer_parts.append("\n---\n")
        answer_parts.append(calc.format_quote(result))

    answer = "\n".join(answer_parts) if answer_parts else "죄송합니다. 요청을 이해하지 못했습니다. 다시 말씀해주세요."

    elapsed_time = time.time() - start_time
    metrics = {
        "response_time": elapsed_time,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "total_tokens": response.total_tokens,
        "cost": response.estimated_cost,
        "llm_provider": settings["llm_provider"],
    }

    return answer, metrics


def process_search_query(query: str, settings: dict) -> tuple[str, list[SearchResult], dict]:
    """
    검색 기반 질문 처리

    Returns:
        (답변, 검색 결과, 메트릭)
    """
    start_time = time.time()

    # 1. 검색 실행
    search_manager = get_search_manager()
    search_results, used_search = search_manager.search(
        query=query,
        provider_name=settings["search_provider"],
        max_results=settings["max_results"],
        use_fallback=settings["use_fallback"]
    )

    # 2. 프롬프트 구성
    system_prompt = get_system_prompt(compact=settings["compact_mode"])
    user_prompt = build_user_prompt(
        query=query,
        search_results=search_results,
        compact=settings["compact_mode"]
    )

    # 3. LLM 답변 생성
    llm_manager = get_llm_manager()
    response = llm_manager.generate(
        prompt=user_prompt,
        provider_name=settings["llm_provider"],
        system_prompt=system_prompt,
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=settings["temperature"]
    )

    # 4. 메트릭 계산
    elapsed_time = time.time() - start_time
    metrics = {
        "response_time": elapsed_time,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "total_tokens": response.total_tokens,
        "cost": response.estimated_cost,
        "search_provider": used_search or settings["search_provider"],
        "llm_provider": settings["llm_provider"],
    }

    return response.content, search_results, metrics


def render_search_chatbot(settings: dict):
    """검색 챗봇 인터페이스"""
    st.subheader("🔍 검색 챗봇")

    # 채팅 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 검색 결과 표시
    if st.session_state.search_results:
        with st.expander(f"🔍 검색 결과 ({len(st.session_state.search_results)}건)", expanded=False):
            for i, r in enumerate(st.session_state.search_results, 1):
                st.markdown(f"""
**[{i}] [{r.title}]({r.url})**
{r.snippet[:200]}{'...' if len(r.snippet) > 200 else ''}
""")
                if i < len(st.session_state.search_results):
                    st.divider()

    # 입력창
    if prompt := st.chat_input("건강기능식품에 대해 질문하세요..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("검색 및 답변 생성 중..."):
                answer, search_results, metrics = process_search_query(prompt, settings)

                if answer:
                    st.markdown(answer)
                else:
                    st.error("답변 생성에 실패했습니다.")

                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.session_state.search_results = search_results
                st.session_state.last_metrics = metrics

        st.rerun()


def main():
    """메인 함수"""
    init_session_state()

    # 타이틀
    st.title(f"{APP_ICON} {APP_TITLE}")

    # 사이드바
    settings = render_sidebar()

    # 모드에 따른 메인 영역 렌더링
    if settings["mode"] == "OEM 견적":
        st.caption("건강기능식품 OEM 자동 견적 시스템")

        tab1, tab2 = st.tabs(["📝 빠른 견적", "💬 대화형 견적"])

        with tab1:
            result = render_quick_quote_form()
            if result:
                render_quote_result(result)
            elif st.session_state.last_quote:
                render_quote_result(st.session_state.last_quote)

        with tab2:
            render_chat_interface(settings)

    else:  # 검색 챗봇
        st.caption("검색 API + LLM 조합 테스트")
        render_search_chatbot(settings)


if __name__ == "__main__":
    main()
