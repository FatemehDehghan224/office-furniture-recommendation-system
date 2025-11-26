from typing import List
from models.sofa_model import OfficeProductEntry, UserRequest


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

def recommend_products(request: UserRequest, products: List[OfficeProductEntry], top_k: int = 5):
    """Return top_k recommended products based on scoring and price proximity"""
    scored = []

    for p in products:
        s = score_product(p, request)
        if s >= 0:
            if request.budget_min is not None and request.budget_max is not None:
                target_price = (request.budget_min + request.budget_max) / 2
            else:
                target_price = request.budget or p.budget
            price_diff = abs(p.budget - target_price)
            scored.append((s, price_diff, p))

    scored.sort(key=lambda x: (-x[0], x[1]))

    return [p for _, _, p in scored[:top_k]]

