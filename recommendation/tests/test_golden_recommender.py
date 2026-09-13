import unittest

from recommendation.models.sofa_model import UserRequest
from recommendation.recommend.recommender import recommend_products
from recommendation.utils.loader import load_products


class GoldenRecommenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.products = load_products()

    def assert_recommended_ids(self, expected, **request_data):
        request = UserRequest(**request_data)
        actual = [item.id for item in recommend_products(request, self.products)]
        self.assertEqual(expected, actual)

    def test_manager_desk_exact_budget_preferences(self):
        self.assert_recommended_ids(
            [2, 4, 39, 3, 5],
            person="manager",
            productType="office desk",
            number_of_person=1,
            budget=15_000_000,
            style="modern",
            color="white",
        )

    def test_employee_chair(self):
        self.assert_recommended_ids(
            [25, 23, 21, 46, 22],
            person="employee",
            productType="office chair",
            number_of_person=1,
            budget=12_000_000,
            style="minimal",
            color="black",
        )

    def test_guest_sofa_budget_range(self):
        self.assert_recommended_ids(
            [47, 60, 68, 50, 62],
            person="guest",
            productType="waiting area sofa",
            number_of_person=3,
            budget_min=10_000_000,
            budget_max=25_000_000,
            style="modern",
            color="gray",
        )

    def test_low_budget_still_returns_nearest_candidates(self):
        self.assert_recommended_ids(
            [2, 3, 4, 49, 5],
            person="manager",
            productType="office desk",
            number_of_person=1,
            budget=1,
        )

    def test_catalog_snapshot(self):
        self.assertEqual(70, len(self.products))
        self.assertEqual(70, len({item.id for item in self.products}))


if __name__ == "__main__":
    unittest.main()
