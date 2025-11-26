from models.sofa_model import UserRequest, UserType, ProductType, Style, Color
from utils.loader import load_products
from recommend.recommender import recommend_products

req = UserRequest(
    person=UserType.manager,
    productType=ProductType.desk,
    number_of_person=1,
    budget=15000000,
    style=Style.modern,
    color=Color.white
)

def test_recommender(user_request: UserRequest):
    products = load_products()

    recs = recommend_products(user_request, products)

    print("Top recommendations:")
    for r in recs:
        print(f"ID={r.id}, Style={r.style.value}, Color={r.color.value}, Budget={r.budget:,}")