"""
견적 계산 서비스
- 원료비 계산
- 부재료비 계산 (포장재)
- 임가공비 계산
- MOQ 규칙 적용
- 총 견적 산출
"""

from dataclasses import dataclass, field
from typing import Optional

from .ingredient import IngredientService


@dataclass
class ProductSpec:
    """제품 사양"""
    product_type: str  # 환, 분말, 정제, 과립
    gram_per_pouch: float  # 1포당 그램
    pouch_per_box: int  # 1박스당 포수
    boxes: int  # 총 박스 수
    ingredient_ratios: dict[str, float] = field(default_factory=dict)  # 원료별 비율

    @property
    def total_pouches(self) -> int:
        """총 포수"""
        return self.pouch_per_box * self.boxes

    @property
    def total_kg(self) -> float:
        """총 원료량 (kg)"""
        return self.gram_per_pouch * self.pouch_per_box * self.boxes / 1000


@dataclass
class QuoteResult:
    """견적 결과"""
    product_spec: ProductSpec
    ingredient_cost: int  # 원료비
    packaging_cost: int  # 포장비
    processing_cost: int  # 임가공비
    total_cost: int  # 총 비용
    price_per_box: int  # 박스당 가격
    moq_applied: bool  # MOQ 적용 여부
    original_boxes: int  # 원래 요청 박스 수

    # 상세 내역
    ingredient_details: list[dict] = field(default_factory=list)
    packaging_details: dict = field(default_factory=dict)
    processing_details: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


class QuoteCalculator:
    """OEM 견적 계산기"""

    def __init__(self, ingredient_service: Optional[IngredientService] = None):
        """
        Args:
            ingredient_service: 원료 서비스 (기본값: 새로 생성)
        """
        self.ingredient_svc = ingredient_service or IngredientService()

    def calculate(self, spec: ProductSpec) -> QuoteResult:
        """
        견적 계산

        Args:
            spec: 제품 사양

        Returns:
            견적 결과
        """
        warnings = []
        original_boxes = spec.boxes

        # 1. MOQ 적용
        moq_applied, spec = self._apply_moq(spec)
        if moq_applied:
            warnings.append(
                f"MOQ 적용: {original_boxes}박스 → {spec.boxes}박스로 조정됨"
            )

        # 2. 원료비 계산
        ingredient_result = self._calculate_ingredient_cost(spec)
        ingredient_cost = ingredient_result["total_cost"]
        ingredient_details = ingredient_result["details"]

        if ingredient_result["missing_ingredients"]:
            warnings.append(
                f"DB에 없는 원료: {', '.join(ingredient_result['missing_ingredients'])}"
            )

        # 3. 포장비 계산
        packaging_result = self._calculate_packaging_cost(spec)
        packaging_cost = packaging_result["total_cost"]
        packaging_details = packaging_result

        # 4. 임가공비 계산
        processing_result = self._calculate_processing_cost(spec)
        processing_cost = processing_result["total_cost"]
        processing_details = processing_result

        if processing_result.get("warning"):
            warnings.append(processing_result["warning"])

        # 5. 총 견적
        total_cost = ingredient_cost + packaging_cost + processing_cost
        price_per_box = int(total_cost / spec.boxes) if spec.boxes > 0 else 0

        return QuoteResult(
            product_spec=spec,
            ingredient_cost=ingredient_cost,
            packaging_cost=packaging_cost,
            processing_cost=processing_cost,
            total_cost=total_cost,
            price_per_box=price_per_box,
            moq_applied=moq_applied,
            original_boxes=original_boxes,
            ingredient_details=ingredient_details,
            packaging_details=packaging_details,
            processing_details=processing_details,
            warnings=warnings,
        )

    def _apply_moq(self, spec: ProductSpec) -> tuple[bool, ProductSpec]:
        """
        MOQ(최소주문수량) 규칙 적용

        Returns:
            (MOQ 적용 여부, 조정된 ProductSpec)
        """
        moq_rules = self.ingredient_svc.get_moq_rules()
        min_boxes = moq_rules.get("default_moq_boxes", 2000)
        min_kg = moq_rules.get("min_production_kg", 300)

        applied = False

        # 박스 수 MOQ 체크
        if spec.boxes < min_boxes:
            spec = ProductSpec(
                product_type=spec.product_type,
                gram_per_pouch=spec.gram_per_pouch,
                pouch_per_box=spec.pouch_per_box,
                boxes=min_boxes,
                ingredient_ratios=spec.ingredient_ratios,
            )
            applied = True

        # 최소 생산량(kg) 체크
        if spec.total_kg < min_kg:
            # 최소 kg를 충족하는 박스 수 계산
            kg_per_box = spec.gram_per_pouch * spec.pouch_per_box / 1000
            required_boxes = int(min_kg / kg_per_box) + 1
            spec = ProductSpec(
                product_type=spec.product_type,
                gram_per_pouch=spec.gram_per_pouch,
                pouch_per_box=spec.pouch_per_box,
                boxes=max(spec.boxes, required_boxes),
                ingredient_ratios=spec.ingredient_ratios,
            )
            applied = True

        return applied, spec

    def _calculate_ingredient_cost(self, spec: ProductSpec) -> dict:
        """원료비 계산"""
        return self.ingredient_svc.calculate_ingredient_cost(
            ratios=spec.ingredient_ratios,
            total_kg=spec.total_kg
        )

    def _calculate_packaging_cost(self, spec: ProductSpec) -> dict:
        """포장비 계산"""
        # 스틱 포장비
        stick_info = self.ingredient_svc.get_packaging_cost("스틱포장")
        stick_cost = spec.total_pouches * stick_info["price"] if stick_info else 0

        # 단박스 포장비
        box_info = self.ingredient_svc.get_packaging_cost("단박스")
        box_cost = spec.boxes * box_info["price"] if box_info else 0

        return {
            "stick": {
                "count": spec.total_pouches,
                "unit_price": stick_info["price"] if stick_info else 0,
                "cost": stick_cost,
            },
            "box": {
                "count": spec.boxes,
                "unit_price": box_info["price"] if box_info else 0,
                "cost": box_cost,
            },
            "total_cost": stick_cost + box_cost,
        }

    def _calculate_processing_cost(self, spec: ProductSpec) -> dict:
        """임가공비 계산"""
        processing_info = self.ingredient_svc.get_processing_cost(spec.product_type)

        if not processing_info:
            return {
                "type": spec.product_type,
                "kg": spec.total_kg,
                "unit_price": 0,
                "total_cost": 0,
                "warning": f"알 수 없는 제형: {spec.product_type}",
            }

        total_cost = int(spec.total_kg * processing_info["price"])

        return {
            "type": spec.product_type,
            "kg": spec.total_kg,
            "unit_price": processing_info["price"],
            "total_cost": total_cost,
        }

    def format_quote(self, result: QuoteResult) -> str:
        """
        견적 결과를 포맷팅된 문자열로 변환

        Args:
            result: 견적 결과

        Returns:
            포맷팅된 견적 문자열
        """
        spec = result.product_spec
        lines = []

        lines.append("=" * 50)
        lines.append("【OEM 제품 예상 견적서】")
        lines.append("=" * 50)

        # 제품 정보
        lines.append("\n▶ 제품정보")
        lines.append(f"   제형: {spec.product_type}")
        lines.append(f"   규격: {spec.gram_per_pouch}g × {spec.pouch_per_box}포/박스")
        lines.append(f"   수량: {spec.boxes:,}박스 ({spec.total_pouches:,}포)")
        lines.append(f"   총 원료량: {spec.total_kg:.1f}kg")

        # 원료 구성
        lines.append("\n▶ 원료 구성")
        for item in result.ingredient_details:
            lines.append(
                f"   {item['name']}: {item['ratio']}% ({item['kg']:.1f}kg)"
            )

        # 비용 상세
        lines.append("\n▶ 비용 상세")
        lines.append(f"   1. 원료비: {result.ingredient_cost:,}원")
        for item in result.ingredient_details:
            lines.append(
                f"      - {item['name']}: {item['kg']:.1f}kg × {item['price_per_kg']:,}원 = {item['cost']:,}원"
            )

        pkg = result.packaging_details
        lines.append(f"   2. 포장비: {result.packaging_cost:,}원")
        lines.append(
            f"      - 스틱포장: {pkg['stick']['count']:,}포 × {pkg['stick']['unit_price']}원 = {pkg['stick']['cost']:,}원"
        )
        lines.append(
            f"      - 단박스: {pkg['box']['count']:,}개 × {pkg['box']['unit_price']}원 = {pkg['box']['cost']:,}원"
        )

        proc = result.processing_details
        lines.append(f"   3. 임가공비: {result.processing_cost:,}원")
        lines.append(
            f"      - {proc['type']}비: {proc['kg']:.1f}kg × {proc['unit_price']:,}원"
        )

        # 총액
        lines.append("\n" + "-" * 50)
        lines.append(f"💰 총 예상금액: {result.total_cost:,}원 (VAT 별도)")
        lines.append(f"   박스당 단가: {result.price_per_box:,}원")
        lines.append("-" * 50)

        # 경고 메시지
        if result.warnings:
            lines.append("\n⚠️ 참고사항")
            for warning in result.warnings:
                lines.append(f"   - {warning}")

        return "\n".join(lines)
