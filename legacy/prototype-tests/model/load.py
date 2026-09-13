import json
from pathlib import Path
from models import OfficeProductEntry, UserType, ProductType, Style, Color, FabricMaterial, BodyMaterial

def load_json_file(json_path: str):
    """
    Reads the hierarchical sofa.json file and flattens it into a list of OfficeProductEntry
    """
    path = Path(json_path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    products = []
    for person_str, product_types in data.items():
        person = UserType(person_str)
        for product_type_str, items in product_types.items():
            product_type = ProductType(product_type_str)
            for item in items:
                entry = OfficeProductEntry(
                    id=item["id"],
                    productType=product_type,
                    person=person,
                    number_of_person=item["number_of_person"],
                    budget=item["budget"],
                    style=Style(item["style"]),
                    color=Color(item["color"]),
                    fabric_material=FabricMaterial(item["fabric_material"]) if item["fabric_material"] else FabricMaterial.unknown,
                    body_material=BodyMaterial(item["body_material"]) if item["body_material"] else BodyMaterial.unknown,
                )
                products.append(entry)

    return products

def load_products():
    BASE_DIR = Path(__file__).resolve().parent
    DATA_FILE = BASE_DIR / "sofa.json"

    products = load_json_file(DATA_FILE)
    print(f"Loaded {len(products)} products")
