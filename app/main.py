"""
AI POC - 건강기능식품 검색 챗봇
Streamlit 메인 앱
"""

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
from app.utils.prompt import (
    get_system_prompt,
    build_user_prompt,
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


def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        st.header("⚙️ 설정")

        # 검색 API 선택
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
                help="검색 실패 시 다른 API 시도"
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
            st.caption(f"검색: {metrics.get('search_provider', '-')}")
            st.caption(f"LLM: {metrics.get('llm_provider', '-')}")
        else:
            st.caption("아직 요청 없음")

        # 초기화 버튼
        if st.button("🗑️ 대화 초기화"):
            st.session_state.messages = []
            st.session_state.search_results = []
            st.session_state.last_metrics = {}
            st.rerun()

        return {
            "search_provider": search_provider,
            "llm_provider": llm_provider,
            "max_results": max_results if 'max_results' in dir() else DEFAULT_SEARCH_RESULTS,
            "temperature": temperature if 'temperature' in dir() else DEFAULT_TEMPERATURE,
            "compact_mode": compact_mode if 'compact_mode' in dir() else False,
            "use_fallback": use_fallback if 'use_fallback' in dir() else True,
        }


def render_chat_messages():
    """채팅 메시지 렌더링"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def render_search_results(results: list[SearchResult]):
    """검색 결과 렌더링"""
    if not results:
        return

    with st.expander(f"🔍 검색 결과 ({len(results)}건)", expanded=False):
        for i, r in enumerate(results, 1):
            st.markdown(f"""
**[{i}] [{r.title}]({r.url})**
{r.snippet[:200]}{'...' if len(r.snippet) > 200 else ''}
<small>출처: {r.source}</small>
""", unsafe_allow_html=True)
            if i < len(results):
                st.divider()


def process_query(query: str, settings: dict) -> tuple[str, list[SearchResult], dict]:
    """
    질문 처리: 검색 → LLM 답변 생성

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


def main():
    """메인 함수"""
    init_session_state()

    # 타이틀
    st.title(f"{APP_ICON} {APP_TITLE}")
    st.caption("검색 API + LLM 조합 테스트 POC")

    # 사이드바
    settings = render_sidebar()

    # 메인 영역
    col1, col2 = st.columns([2, 1])

    with col1:
        # 채팅 메시지 표시
        render_chat_messages()

        # 검색 결과 표시
        if st.session_state.search_results:
            render_search_results(st.session_state.search_results)

    with col2:
        # 현재 설정 요약
        st.info(f"""
**현재 설정**
- 검색: {settings['search_provider']}
- LLM: {settings['llm_provider']}
- 토큰절약: {'ON' if settings['compact_mode'] else 'OFF'}
""")

    # 입력창
    if prompt := st.chat_input("건강기능식품에 대해 질문하세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # 답변 생성
        with st.chat_message("assistant"):
            with st.spinner("검색 및 답변 생성 중..."):
                answer, search_results, metrics = process_query(prompt, settings)

                if answer:
                    st.markdown(answer)
                else:
                    st.error("답변 생성에 실패했습니다. API 키를 확인해주세요.")

                # 상태 저장
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.session_state.search_results = search_results
                st.session_state.last_metrics = metrics

        st.rerun()


if __name__ == "__main__":
    main()
