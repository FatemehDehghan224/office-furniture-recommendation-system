from dataclasses import dataclass
from typing import Any

from django.db import transaction

from apps.products.models import Product
from apps.recommendations.models import RecommendationRequest, RecommendationResult
from recommendation.models.sofa_model import OfficeProductEntry, UserRequest
from recommendation.recommend.recommender import rank_products


@dataclass(frozen=True)
class StoredRecommendation:
    product: Product
    score: int
    price_difference: float
    rank: int


def product_to_domain(product: Product) -> OfficeProductEntry:
    return OfficeProductEntry(
        id=product.legacy_id,
        person=product.audience,
        productType=product.product_type,
        number_of_person=product.number_of_person,
        budget=product.budget,
        style=product.style,
        color=product.color,
        fabric_material=product.fabric_material,
        body_material=product.body_material,
    )


@transaction.atomic
def create_recommendation(data: dict[str, Any], top_k: int = 5):
    request = UserRequest(**data)
    candidates = list(
        Product.objects.filter(
            is_active=True,
            audience=request.person.value,
            product_type=request.productType.value,
        )
    )
    products_by_legacy_id = {product.legacy_id: product for product in candidates}
    ranked = rank_products(request, [product_to_domain(item) for item in candidates])[:top_k]

    request_record = RecommendationRequest.objects.create(
        person=request.person.value,
        product_type=request.productType.value,
        number_of_person=request.number_of_person,
        budget=request.budget,
        budget_min=request.budget_min,
        budget_max=request.budget_max,
        style=request.style.value if request.style else None,
        color=request.color.value if request.color else None,
        fabric_material=request.fabric_material.value if request.fabric_material else None,
        body_material=request.body_material.value if request.body_material else None,
    )

    stored = [
        StoredRecommendation(
            product=products_by_legacy_id[item.product.id],
            score=item.score,
            price_difference=item.price_difference,
            rank=index,
        )
        for index, item in enumerate(ranked, start=1)
    ]
    RecommendationResult.objects.bulk_create(
        [
            RecommendationResult(
                request=request_record,
                product=item.product,
                rank=item.rank,
                score=item.score,
                price_difference=item.price_difference,
            )
            for item in stored
        ]
    )
    return request_record, stored
