from typing import Dict, Any
from recommendation.models.sofa_model import (
    UserRequest, UserType, ProductType, Style, Color,
    FabricMaterial, BodyMaterial
)

def map_json_to_user_request(user_input: Dict[str, Any]) -> UserRequest:
    """
    Map the collected user_input dictionary (from LLM JSON)
    into a strongly-typed UserRequest object.
    """
    def safe_enum(enum_class, value, default=None):
        if value is None:
            return default
        try:
            return enum_class(value)
        except ValueError:
            return default

    return UserRequest(
        person=safe_enum(UserType, user_input.get("person")),
        productType=safe_enum(ProductType, user_input.get("productType")),
        number_of_person=int(user_input["number_of_person"]) if user_input.get("number_of_person") is not None else None,
        budget=int(user_input["budget"]) if user_input.get("budget") is not None else None,
        budget_min=int(user_input["budget_min"]) if user_input.get("budget_min") is not None else None,
        budget_max=int(user_input["budget_max"]) if user_input.get("budget_max") is not None else None,
        style=safe_enum(Style, user_input.get("style")),
        color=safe_enum(Color, user_input.get("color")),
        fabric_material=safe_enum(FabricMaterial, user_input.get("fabric_material"), FabricMaterial.unknown),
        body_material=safe_enum(BodyMaterial, user_input.get("body_material"), BodyMaterial.unknown),
    )
