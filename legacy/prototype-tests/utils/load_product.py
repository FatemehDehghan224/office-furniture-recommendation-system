import json
from typing import List
from pydantic import ValidationError
from tests.model.models import OfficeProductEntry


def load_hierarchical_products(path: str) -> List[OfficeProductEntry]:
    """
    Read hierarchical JSON and flatten into list of OfficeProductEntry.
    JSON expected like:
    {
      "manager": {
        "office desk": [ {id:..., number_of_person:..., ...}, ... ],
        ...
      },
      "employee": {...},
      "guest": {...}
    }
    """
    with open(path, "r", encoding="utf-8") as f:
        tree = json.load(f)

    flat = []
    for person_key, types in tree.items():
        for type_key, items in types.items():
            for item in items:
                # build unified record
                record = {
                    "id": item["id"],
                    "productType": type_key,
                    "person": person_key,
                    "number_of_person": item.get("number_of_person", 1),
                    "budget": item.get("budget", 0),
                    "style": item.get("style", None),
                    "color": item.get("color", None),
                    "fabric_material": item.get("fabric_material", "") or "",
                    "body_material": item.get("body_material", "") or ""
                }
                try:
                    entry = OfficeProductEntry.parse_obj(record)
                    flat.append(entry)
                except ValidationError as e:
                    # skip invalid product but log
                    print(f"[load] validation error for product id={item.get('id')}: {e}")
    return flat