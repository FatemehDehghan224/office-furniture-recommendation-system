from dataclasses import dataclass
from typing import List
from recommendation.models.sofa_model import OfficeProductEntry, UserRequest


@dataclass(frozen=True)
class ScoredProduct:
    product: OfficeProductEntry
    score: int
    price_difference: float


def score_product(product: OfficeProductEntry, request: UserRequest) -> int:
    """Calculate score for a single product based on request"""
    score = 0

    if product.person != request.person:
        return -1
    if product.productType != request.productType:
        return -1

    if product.number_of_person >= request.number_of_person:
        score += 1

    if request.budget_min is not None and request.budget_max is not None:
        if request.budget_min <= product.budget <= request.budget_max:
            score += 2
        elif product.budget <= request.budget_max:
            score += 1
    elif request.budget is not None:
        if product.budget <= request.budget:
            score += 1
            if abs(product.budget - request.budget) <= request.budget * 0.2:
                score += 1

    if request.style and product.style == request.style:
        score += 1
    if request.color and product.color == request.color:
        score += 1

    return score

def rank_products(request: UserRequest, products: List[OfficeProductEntry]) -> List[ScoredProduct]:
    """Rank compatible products without changing the original scoring rules."""
    scored: List[ScoredProduct] = []

    for p in products:
        s = score_product(p, request)
        if s >= 0:
            if request.budget_min is not None and request.budget_max is not None:
                target_price = (request.budget_min + request.budget_max) / 2
            else:
                target_price = request.budget or p.budget
            price_diff = abs(p.budget - target_price)
            scored.append(ScoredProduct(product=p, score=s, price_difference=price_diff))

    scored.sort(key=lambda item: (-item.score, item.price_difference))
    return scored


def recommend_products(request: UserRequest, products: List[OfficeProductEntry], top_k: int = 5):
    """Return top_k recommended products based on scoring and price proximity."""
    return [item.product for item in rank_products(request, products)[:top_k]]

