import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from models.sofa_model import OfficeProductEntry, UserType, ProductType, Style, Color, FabricMaterial, BodyMaterial

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
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_FILE = BASE_DIR / "data" / "sofa.json"

    products = load_json_file(DATA_FILE)
    return products

def show_products():
    products = load_products()

    table = Table(title="Office Products")
    table.add_column("ID", justify="center", style="cyan")
    table.add_column("Person", justify="center", style="magenta")
    table.add_column("Type", justify="center", style="green")
    table.add_column("Style", justify="center", style="yellow")
    table.add_column("Color", justify="center", style="blue")
    table.add_column("Budget", justify="center", style="red")

    for product in products:
        table.add_row(
            str(product.id),
            product.person.value,
            product.productType.value,
            product.style.value,
            product.color.value,
            f"{product.budget:,}"
        )

    console = Console()
    console.print(table)

# show_products()