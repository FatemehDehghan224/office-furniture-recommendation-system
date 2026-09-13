from typing import Dict, Any
from pydantic import ValidationError
from tests.model.models import UserType, ProductType, Style, Color, FabricMaterial, BodyMaterial, UserRequest

def cli_collect_user_input() -> Dict[str, Any]:
    print("Interactive CLI: Please answer questions (press Enter for 'no preference' where allowed).")
    def ask_enum(field_name, enum_cls):
        vals = [v.value for v in enum_cls]
        print(f"{field_name} options: {vals}")
        ans = input(f"{field_name}: ").strip()
        if ans == "":
            return None
        if ans in vals:
            return ans
        # try case-insensitive match
        for v in vals:
            if ans.lower() == v.lower():
                return v
        print("Invalid choice. Using None.")
        return None

    person = ask_enum("person (manager/employee/guest)", UserType) or default_user_type()
    productType = ask_enum("productType", ProductType) or default_product_type_for_person(person)
    try:
        number_of_person = int(input("number_of_person (e.g., 1): ").strip() or "1")
    except:
        number_of_person = 1
    try:
        budget = int(input("budget (integer): ").strip() or "0")
    except:
        budget = 0
    style = ask_enum("style", Style)
    color = ask_enum("color", Color)
    fabric_material = ask_enum("fabric_material", FabricMaterial)
    body_material = ask_enum("body_material", BodyMaterial)
    req = {
        "person": person,
        "productType": productType,
        "number_of_person": number_of_person,
        "budget": budget,
        "style": style,
        "color": color,
        "fabric_material": fabric_material or "",
        "body_material": body_material or ""
    }
    # validate
    try:
        UserRequest.parse_obj(req)
    except ValidationError as e:
        print("Validation error:", e)
        raise
    return req

def default_user_type() -> str:
    return UserType.employee.value

def default_product_type_for_person(person: str) -> str:
    # sensible defaults
    mapping = {
        "manager": ProductType.desk.value,
        "employee": ProductType.desk.value,
        "guest": ProductType.waiting_area_sofa.value
    }
    return mapping.get(person, ProductType.desk.value)
