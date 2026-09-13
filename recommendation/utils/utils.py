import json
from typing import List
from pathlib import Path
from recommendation.models.sofa_model import OfficeProductEntry

def products_to_json(products: List[OfficeProductEntry]) -> str:
    """
    Convert a list of OfficeProductEntry objects into a JSON string.
    """
    return json.dumps([p.dict() for p in products], indent=2, ensure_ascii=False)

def load_system_prompt(prompt_path: str) -> str:
    """Load system prompt text file."""
    base_dir = Path(__file__).resolve().parent
    path = base_dir / prompt_path
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return f.read()

def entry_to_json(entry):
    return {
        "id": entry.id,
        "productType": entry.productType.value,
        "person": entry.person.value,
        "number_of_person": entry.number_of_person,
        "budget": entry.budget,
        "style": entry.style.value,
        "color": entry.color.value,
        "fabric_material": entry.fabric_material.value if entry.fabric_material else "",
        "body_material": entry.body_material.value if entry.body_material else ""
    }
