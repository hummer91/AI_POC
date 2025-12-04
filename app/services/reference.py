"""
레퍼런스 제품 검색 서비스
- DB 레퍼런스 제품 조회
- 시중 제품 검색 (검색 API 활용)
- 배합비 추출/제안
"""

from dataclasses import dataclass, field
from typing import Optional

from ..providers.search import SearchManager, SearchResult, get_search_manager
from .ingredient import IngredientService


@dataclass
class ReferenceProduct:
    """레퍼런스 제품 정보"""
    name: str
    source: str  # "db" 또는 검색 provider 이름
    ratio: dict[str, float] = field(default_factory=dict)  # 배합비 (DB 제품만)
    url: Optional[str] = None  # 검색 결과 URL
    snippet: Optional[str] = None  # 검색 결과 요약


class ReferenceService:
    """레퍼런스 제품 검색 및 배합비 제안 서비스"""

    # 건강기능식품 관련 검색 키워드
    SEARCH_SUFFIXES = [
        "건강기능식품 배합비",
        "OEM 원료 비율",
        "성분 함량",
    ]

    def __init__(
        self,
        ingredient_service: Optional[IngredientService] = None,
        search_manager: Optional[SearchManager] = None
    ):
        """
        Args:
            ingredient_service: 원료 서비스
            search_manager: 검색 매니저
        """
        self.ingredient_svc = ingredient_service or IngredientService()
        self.search_mgr = search_manager or get_search_manager()

    def get_db_references(self, ingredient_name: str) -> list[ReferenceProduct]:
        """
        DB에서 레퍼런스 제품 조회

        Args:
            ingredient_name: 주원료명

        Returns:
            레퍼런스 제품 리스트
        """
        db_refs = self.ingredient_svc.get_reference_products(ingredient_name)

        return [
            ReferenceProduct(
                name=ref["name"],
                source="db",
                ratio=ref.get("ratio", {}),
            )
            for ref in db_refs
        ]

    def search_market_products(
        self,
        ingredient_name: str,
        product_type: str = "",
        max_results: int = 5,
        provider_name: Optional[str] = None
    ) -> tuple[list[ReferenceProduct], str]:
        """
        시중 제품 검색 (검색 API 활용)

        Args:
            ingredient_name: 주원료명
            product_type: 제형 (환, 분말 등)
            max_results: 최대 검색 결과 수
            provider_name: 사용할 검색 Provider (None이면 자동 선택)

        Returns:
            (레퍼런스 제품 리스트, 사용된 Provider 이름)
        """
        # 검색 쿼리 생성
        type_str = f" {product_type}" if product_type else ""
        query = f"{ingredient_name}{type_str} 건강기능식품 배합비 성분"

        # 검색 실행
        results, used_provider = self.search_mgr.search(
            query=query,
            provider_name=provider_name,
            max_results=max_results,
            use_fallback=True
        )

        products = [
            ReferenceProduct(
                name=r.title,
                source=used_provider,
                url=r.url,
                snippet=r.snippet,
            )
            for r in results
        ]

        return products, used_provider

    def get_references(
        self,
        ingredient_name: str,
        product_type: str = "",
        include_search: bool = True,
        max_search_results: int = 3,
        search_provider: Optional[str] = None
    ) -> dict:
        """
        통합 레퍼런스 제품 조회 (DB + 검색)

        Args:
            ingredient_name: 주원료명
            product_type: 제형
            include_search: 검색 결과 포함 여부
            max_search_results: 최대 검색 결과 수
            search_provider: 사용할 검색 Provider

        Returns:
            {
                "db_products": DB 레퍼런스 제품 리스트,
                "search_products": 검색 레퍼런스 제품 리스트,
                "search_provider": 사용된 검색 Provider,
                "recommended_ratio": 추천 배합비
            }
        """
        result = {
            "db_products": [],
            "search_products": [],
            "search_provider": None,
            "recommended_ratio": None,
        }

        # 1. DB 레퍼런스 조회
        result["db_products"] = self.get_db_references(ingredient_name)

        # 2. 검색 결과 조회
        if include_search:
            search_products, provider = self.search_market_products(
                ingredient_name=ingredient_name,
                product_type=product_type,
                max_results=max_search_results,
                provider_name=search_provider,
            )
            result["search_products"] = search_products
            result["search_provider"] = provider

        # 3. 추천 배합비 (DB에 있으면 첫 번째 제품의 비율)
        if result["db_products"]:
            first_ref = result["db_products"][0]
            result["recommended_ratio"] = first_ref.ratio

        return result

    def suggest_ratio(
        self,
        ingredient_name: str,
        main_ratio: Optional[float] = None
    ) -> dict[str, float]:
        """
        배합비 제안

        Args:
            ingredient_name: 주원료명
            main_ratio: 주원료 비율 (None이면 레퍼런스 제품 비율 사용)

        Returns:
            추천 배합비 딕셔너리
        """
        # DB 레퍼런스 확인
        db_refs = self.get_db_references(ingredient_name)

        if main_ratio is not None:
            # 사용자가 주원료 비율을 지정한 경우
            # 부형제 자동 추천
            excipients = self.ingredient_svc.recommend_excipients(main_ratio)
            return {ingredient_name: main_ratio, **excipients}

        elif db_refs:
            # DB에 레퍼런스가 있으면 첫 번째 제품 비율 사용
            return db_refs[0].ratio.copy()

        else:
            # 기본값: 주원료 80% + 부형제 자동
            excipients = self.ingredient_svc.recommend_excipients(80)
            return {ingredient_name: 80, **excipients}

    def format_references(
        self,
        ingredient_name: str,
        product_type: str = "",
        include_search: bool = True
    ) -> str:
        """
        레퍼런스 정보를 포맷팅된 문자열로 반환

        Args:
            ingredient_name: 주원료명
            product_type: 제형
            include_search: 검색 결과 포함 여부

        Returns:
            포맷팅된 레퍼런스 정보 문자열
        """
        refs = self.get_references(
            ingredient_name=ingredient_name,
            product_type=product_type,
            include_search=include_search,
        )

        lines = []
        lines.append(f"【{ingredient_name} 레퍼런스 제품】")
        lines.append("")

        # DB 제품
        if refs["db_products"]:
            lines.append("▶ 참고 제품 (DB)")
            for i, prod in enumerate(refs["db_products"], 1):
                ratio_str = ", ".join(
                    f"{k} {v}%" for k, v in prod.ratio.items()
                )
                lines.append(f"   {i}. {prod.name}")
                lines.append(f"      배합비: {ratio_str}")
        else:
            lines.append("▶ DB에 등록된 레퍼런스 제품이 없습니다.")

        # 검색 결과
        if include_search and refs["search_products"]:
            lines.append("")
            lines.append(f"▶ 시중 제품 검색 결과 ({refs['search_provider']})")
            for i, prod in enumerate(refs["search_products"], 1):
                lines.append(f"   {i}. {prod.name}")
                if prod.snippet:
                    # snippet이 너무 길면 잘라내기
                    snippet = prod.snippet[:100] + "..." if len(prod.snippet) > 100 else prod.snippet
                    lines.append(f"      {snippet}")

        # 추천 배합비
        if refs["recommended_ratio"]:
            lines.append("")
            lines.append("▶ 추천 배합비")
            ratio_str = ", ".join(
                f"{k} {v}%" for k, v in refs["recommended_ratio"].items()
            )
            lines.append(f"   {ratio_str}")

        return "\n".join(lines)
