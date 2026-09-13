from typing import Any, Dict, List
from tests.model.models import UserRequest, OfficeProductEntry


class RuleEngine:
    """
    Dynamic rule engine:
    - Mandatory filters:
        - product.person == user.person
        - product.productType == user.productType
        - product.number_of_person >= user.number_of_person
        - product.budget <= user.budget  (we keep products <= budget)
    - Scoring:
        - style exact match: +3
        - color exact match: +2
        - fabric_material exact match and not empty: +1.5
        - body_material exact match and not empty: +1.5
        - budget closeness: + (1 - abs(prod_budget - user_budget)/max(user_budget,1)) clipped to [0,1] then *3
    - returns sorted list of tuples (product, score)
    """
    def __init__(self, products: List[OfficeProductEntry]):
        self.products = products

    def filter_products(self, user: UserRequest) -> List[OfficeProductEntry]:
        res = []
        for p in self.products:
            # mandatory checks
            if p.person != user.person:
                continue
            if p.productType != user.productType:
                continue
            if p.number_of_person < user.number_of_person:
                continue
            # budget filter: allow recommendations with product.budget <= user.budget
            if p.budget > user.budget:
                continue
            res.append(p)
        return res

    def score_product(self, prod: OfficeProductEntry, user: UserRequest) -> float:
        score = 0.0
        # exact style
        if user.style and prod.style == user.style:
            score += 3.0
        # color
        if user.color and prod.color == user.color:
            score += 2.0
        # fabric
        if user.fabric_material and prod.fabric_material == user.fabric_material and prod.fabric_material not in ("", "unknown"):
            score += 1.5
        # body
        if user.body_material and prod.body_material == user.body_material and prod.body_material not in ("", "unknown"):
            score += 1.5
        # budget closeness (normalized)
        if user.budget > 0:
            diff = abs(prod.budget - user.budget) / user.budget
            closeness = max(0.0, 1.0 - diff)  # 1 when exact, 0 when prod.budget >= 2x user.budget
            score += closeness * 3.0
        # small preference boost for exact capacity match
        if prod.number_of_person == user.number_of_person:
            score += 0.5
        return score

    def recommend(self, user: UserRequest, top_k: int = 5) -> List[Dict[str, Any]]:
        filtered = self.filter_products(user)
        scored = []
        for p in filtered:
            sc = self.score_product(p, user)
            scored.append((p, sc))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [{"product": x[0].model_dump(), "score": round(x[1], 3)} for x in scored[:top_k]]
