"""
원료 DB 조회 서비스
- 원료 조회
- 가격 조회
- 부형제 자동 추천
- 레퍼런스 제품 조회
"""

import json
from pathlib import Path
from typing import Optional


class IngredientService:
    """원료 DB 조회 및 관리 서비스"""

    # 기본 부형제 비율 (주원료 비율이 100%가 아닐 때 자동 채움)
    DEFAULT_EXCIPIENTS = {
        "결정셀룰로스": 10,  # 충전제
        "정제포도당": 8,     # 감미료
        "이산화규소": 1,     # 유동화제
        "스테아린산마그네슘": 1,  # 활택제
    }

    def __init__(self, db_path: Optional[str] = None):
        """
        Args:
            db_path: 원료 DB JSON 파일 경로 (기본값: data/ingredient_db.json)
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "ingredient_db.json"

        self.db_path = Path(db_path)
        self._load_db()

    def _load_db(self):
        """원료 DB 로드"""
        with open(self.db_path, "r", encoding="utf-8") as f:
            self._db = json.load(f)

        self.ingredients = self._db.get("ingredients", {})
        self.processing_costs = self._db.get("processing_costs", {})
        self.packaging_costs = self._db.get("packaging_costs", {})
        self.moq_rules = self._db.get("moq_rules", {})
        self.product_types = self._db.get("product_types", {})
        self.reference_products = self._db.get("reference_products", {})

    def search_ingredient(self, keyword: str) -> list[dict]:
        """
        원료명으로 검색

        Args:
            keyword: 검색할 원료명 (부분 일치)

        Returns:
            매칭된 원료 정보 리스트
        """
        results = []
        keyword_lower = keyword.lower()

        for name, info in self.ingredients.items():
            if keyword_lower in name.lower():
                results.append({
                    "name": name,
                    "price_per_kg": info["price_per_kg"],
                    "category": info["category"],
                    "description": info["description"]
                })

        return results

    def get_ingredient(self, name: str) -> Optional[dict]:
        """
        정확한 원료명으로 조회

        Args:
            name: 원료명

        Returns:
            원료 정보 또는 None
        """
        if name in self.ingredients:
            info = self.ingredients[name]
            return {
                "name": name,
                "price_per_kg": info["price_per_kg"],
                "category": info["category"],
                "description": info["description"]
            }
        return None

    def get_price(self, name: str) -> Optional[int]:
        """
        원료 가격 조회 (kg당)

        Args:
            name: 원료명

        Returns:
            kg당 가격 (원) 또는 None
        """
        ingredient = self.ingredients.get(name)
        if ingredient:
            return ingredient["price_per_kg"]
        return None

    def get_excipients(self) -> list[dict]:
        """
        부형제 목록 조회

        Returns:
            부형제 카테고리의 원료 리스트
        """
        return [
            {"name": name, **info}
            for name, info in self.ingredients.items()
            if info["category"] == "부형제"
        ]

    def recommend_excipients(self, main_ratio: float) -> dict[str, float]:
        """
        부형제 자동 추천 (주원료 비율에 맞춰 나머지 채움)

        Args:
            main_ratio: 주원료 비율 (0-100)

        Returns:
            추천 부형제 비율 딕셔너리 {"부형제명": 비율, ...}
        """
        if main_ratio >= 100:
            return {}

        remaining = 100 - main_ratio

        # 기본 부형제 비율의 합계
        total_default = sum(self.DEFAULT_EXCIPIENTS.values())

        # 남은 비율에 맞게 스케일링
        scale = remaining / total_default

        result = {}
        for name, default_ratio in self.DEFAULT_EXCIPIENTS.items():
            scaled_ratio = round(default_ratio * scale, 1)
            if scaled_ratio > 0:
                result[name] = scaled_ratio

        # 반올림 오차 보정 (가장 큰 비율의 부형제에 추가)
        total_result = sum(result.values())
        diff = round(remaining - total_result, 1)

        if diff != 0 and result:
            max_key = max(result, key=result.get)
            result[max_key] = round(result[max_key] + diff, 1)

        return result

    def get_reference_products(self, ingredient_name: str) -> list[dict]:
        """
        원료에 대한 레퍼런스 제품 조회

        Args:
            ingredient_name: 주원료명

        Returns:
            레퍼런스 제품 리스트
        """
        return self.reference_products.get(ingredient_name, [])

    def get_processing_cost(self, product_type: str) -> Optional[dict]:
        """
        제형별 임가공비 조회

        Args:
            product_type: 제형 (환, 분말, 정제, 과립)

        Returns:
            임가공비 정보 또는 None
        """
        type_info = self.product_types.get(product_type)
        if type_info:
            cost_key = type_info["processing_cost_key"]
            return self.processing_costs.get(cost_key)
        return None

    def get_packaging_cost(self, packaging_type: str) -> Optional[dict]:
        """
        포장 비용 조회

        Args:
            packaging_type: 포장 유형 (스틱포장, 단박스, 병포장)

        Returns:
            포장비 정보 또는 None
        """
        return self.packaging_costs.get(packaging_type)

    def get_moq_rules(self) -> dict:
        """MOQ 규칙 조회"""
        return self.moq_rules

    def calculate_ingredient_cost(
        self,
        ratios: dict[str, float],
        total_kg: float
    ) -> dict:
        """
        원료 비용 계산

        Args:
            ratios: 원료별 비율 {"원료명": 비율, ...}
            total_kg: 총 원료량 (kg)

        Returns:
            {
                "details": [{"name": ..., "kg": ..., "price": ..., "cost": ...}, ...],
                "total_cost": 총 원료비,
                "missing_ingredients": [DB에 없는 원료명 리스트]
            }
        """
        details = []
        total_cost = 0
        missing = []

        for name, ratio in ratios.items():
            kg = total_kg * (ratio / 100)
            price = self.get_price(name)

            if price is None:
                missing.append(name)
                continue

            cost = int(kg * price)
            details.append({
                "name": name,
                "ratio": ratio,
                "kg": round(kg, 2),
                "price_per_kg": price,
                "cost": cost
            })
            total_cost += cost

        return {
            "details": details,
            "total_cost": total_cost,
            "missing_ingredients": missing
        }

    def list_all_ingredients(self) -> list[dict]:
        """모든 원료 목록 조회"""
        return [
            {"name": name, **info}
            for name, info in self.ingredients.items()
        ]

    def list_product_types(self) -> list[str]:
        """지원하는 제형 목록"""
        return list(self.product_types.keys())
