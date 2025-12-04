"""
검색 API Provider 모듈
- DDGS (DuckDuckGo)
- Brave Search
- Tavily
- Google Custom Search
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import requests


@dataclass
class SearchResult:
    """검색 결과 데이터 클래스"""
    title: str
    url: str
    snippet: str
    source: str  # 어떤 검색 API에서 왔는지


class SearchProvider(ABC):
    """검색 Provider 베이스 클래스"""

    name: str = "base"

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """검색 실행"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """API 사용 가능 여부 확인"""
        pass


class DDGSProvider(SearchProvider):
    """DuckDuckGo 검색 (무료, 키 불필요)"""

    name = "DDGS"

    def __init__(self):
        try:
            from duckduckgo_search import DDGS
            self._ddgs_class = DDGS
            self._available = True
        except ImportError:
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self.is_available():
            return []

        try:
            with self._ddgs_class() as ddgs:
                results = ddgs.text(query, max_results=max_results)
                return [
                    SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", ""),
                        source=self.name
                    )
                    for r in results
                ]
        except Exception as e:
            print(f"[DDGS] 검색 오류: {e}")
            return []


class BraveSearchProvider(SearchProvider):
    """Brave Search API (2,000회/월 무료)"""

    name = "Brave"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self.is_available():
            return []

        try:
            headers = {
                "X-Subscription-Token": self.api_key,
                "Accept": "application/json"
            }
            params = {
                "q": query,
                "count": max_results
            }

            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("web", {}).get("results", [])[:max_results]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source=self.name
                ))
            return results

        except Exception as e:
            print(f"[Brave] 검색 오류: {e}")
            return []


class TavilyProvider(SearchProvider):
    """Tavily API (1,000회/월 무료, AI 검색 특화)"""

    name = "Tavily"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.base_url = "https://api.tavily.com/search"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self.is_available():
            return []

        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic"
            }

            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", [])[:max_results]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source=self.name
                ))
            return results

        except Exception as e:
            print(f"[Tavily] 검색 오류: {e}")
            return []


class GoogleCSEProvider(SearchProvider):
    """Google Custom Search API (100회/일 무료)"""

    name = "Google"

    def __init__(self, api_key: Optional[str] = None, cse_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_CSE_API_KEY")
        self.cse_id = cse_id or os.getenv("GOOGLE_CSE_ID")
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def is_available(self) -> bool:
        return bool(self.api_key and self.cse_id)

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self.is_available():
            return []

        try:
            params = {
                "key": self.api_key,
                "cx": self.cse_id,
                "q": query,
                "num": min(max_results, 10)  # Google CSE 최대 10개
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("items", [])[:max_results]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source=self.name
                ))
            return results

        except Exception as e:
            print(f"[Google CSE] 검색 오류: {e}")
            return []


class SearchManager:
    """
    통합 검색 매니저
    - 여러 검색 Provider 관리
    - Fallback 로직 지원
    - 특정 Provider 선택 가능
    """

    PROVIDERS = {
        "DDGS": DDGSProvider,
        "Brave": BraveSearchProvider,
        "Tavily": TavilyProvider,
        "Google": GoogleCSEProvider,
    }

    # Fallback 우선순위 (무료 한도 많은 순)
    FALLBACK_ORDER = ["DDGS", "Brave", "Tavily", "Google"]

    def __init__(self):
        self._providers: dict[str, SearchProvider] = {}
        self._init_providers()

    def _init_providers(self):
        """모든 Provider 초기화"""
        for name, provider_class in self.PROVIDERS.items():
            self._providers[name] = provider_class()

    def get_available_providers(self) -> list[str]:
        """사용 가능한 Provider 목록 반환"""
        return [name for name, provider in self._providers.items() if provider.is_available()]

    def search(
        self,
        query: str,
        provider_name: Optional[str] = None,
        max_results: int = 5,
        use_fallback: bool = True
    ) -> tuple[list[SearchResult], str]:
        """
        검색 실행

        Args:
            query: 검색어
            provider_name: 사용할 Provider (None이면 fallback 순서대로)
            max_results: 최대 결과 수
            use_fallback: 실패 시 다른 Provider 시도 여부

        Returns:
            (검색 결과 리스트, 사용된 Provider 이름)
        """

        # 특정 Provider 지정된 경우
        if provider_name:
            if provider_name in self._providers:
                provider = self._providers[provider_name]
                if provider.is_available():
                    results = provider.search(query, max_results)
                    if results:
                        return results, provider_name
                    elif not use_fallback:
                        return [], provider_name
            elif not use_fallback:
                return [], ""

        # Fallback 로직
        for name in self.FALLBACK_ORDER:
            if provider_name and name == provider_name:
                continue  # 이미 시도한 Provider 스킵

            provider = self._providers.get(name)
            if provider and provider.is_available():
                results = provider.search(query, max_results)
                if results:
                    return results, name

        return [], ""

    def search_all(self, query: str, max_results: int = 5) -> dict[str, list[SearchResult]]:
        """모든 사용 가능한 Provider로 검색 (비교용)"""
        results = {}
        for name in self.get_available_providers():
            provider = self._providers[name]
            results[name] = provider.search(query, max_results)
        return results


# 편의를 위한 싱글톤 인스턴스
_search_manager: Optional[SearchManager] = None

def get_search_manager() -> SearchManager:
    """SearchManager 싱글톤 인스턴스 반환"""
    global _search_manager
    if _search_manager is None:
        _search_manager = SearchManager()
    return _search_manager
