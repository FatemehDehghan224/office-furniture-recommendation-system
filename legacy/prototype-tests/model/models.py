from enum import Enum
from typing import Optional
from pydantic import Field, BaseModel

class ProductType(str, Enum):
    desk = "office desk"
    chair = "office chair"
    cabinet = "file cabinet"
    bookshelf = "bookshelf"
    reception_counter = "reception counter"
    waiting_area_sofa = "waiting area sofa"

class UserType(str, Enum):
    manager = "manager"
    employee = "employee"
    guest = "guest"

class Style(str, Enum):
    modern = "modern"
    classic = "classic"
    minimal = "minimal"
    industrial = "industrial"

class Color(str, Enum):
    black = "black"
    white = "white"
    gray = "gray"
    brown = "brown"
    cream = "cream"

class FabricMaterial(str, Enum):
    leather = "leather"
    linen = "linen"
    unknown = ""

class BodyMaterial(str, Enum):
    wood = "wood"
    aluminum = "aluminum"
    unknown = ""

class OfficeProductModel(BaseModel):
    # product fields stored inside each product item
    id: int
    number_of_person: int
    budget: int
    style: Style
    color: Color
    fabric_material: Optional[FabricMaterial] = FabricMaterial.unknown
    body_material: Optional[BodyMaterial] = BodyMaterial.unknown

class OfficeProductEntry(BaseModel):
    # wrapper: person and productType kept outside in hierarchical JSON,
    # but here we unify a flat representation for searching:
    id: int
    productType: ProductType
    person: UserType
    number_of_person: int
    budget: int
    style: Style
    color: Color
    fabric_material: Optional[FabricMaterial] = FabricMaterial.unknown
    body_material: Optional[BodyMaterial] = BodyMaterial.unknown

class UserRequest(BaseModel):
    person: UserType = Field(..., description="Who is the furniture for (manager/employee/guest)")
    productType: ProductType = Field(..., description="Type of product wanted")
    number_of_person: int = Field(..., description="Seating capacity needed (1,2,3,...)")
    budget: int = Field(..., description="Budget available (integer, same currency as product budgets)")
    style: Optional[Style] = Field(None, description="Preferred design style")
    color: Optional[Color] = Field(None, description="Preferred color")
    fabric_material: Optional[FabricMaterial] = Field(None, description="Preferred upholstery material, if relevant")
    body_material: Optional[BodyMaterial] = Field(None, description="Preferred body/frame material")
