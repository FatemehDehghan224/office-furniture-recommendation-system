import json

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch

from apps.products.models import Product
from apps.recommendations.models import (
    RecommendationFeedback,
    RecommendationRequest,
    RecommendationResult,
)
from recommendation.utils.llm_client import LLMConfigurationError


class RecommendationApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("import_products", verbosity=0)

    def setUp(self):
        self.client = APIClient()

    def test_imported_catalog_matches_legacy_catalog(self):
        self.assertEqual(70, Product.objects.count())
        call_command("import_products", verbosity=0)
        self.assertEqual(70, Product.objects.count())

    def test_recommendation_endpoint_preserves_golden_order(self):
        response = self.client.post(
            reverse("recommendation-create"),
            {
                "person": "manager",
                "productType": "office desk",
                "number_of_person": 1,
                "budget": 15_000_000,
                "style": "modern",
                "color": "white",
            },
            format="json",
        )

        self.assertEqual(201, response.status_code)
        ids = [item["product"]["id"] for item in response.data["recommendations"]]
        self.assertEqual([2, 4, 39, 3, 5], ids)
        self.assertEqual(1, RecommendationRequest.objects.count())
        self.assertEqual(5, RecommendationResult.objects.count())

    def test_range_validation(self):
        response = self.client.post(
            reverse("recommendation-create"),
            {
                "person": "guest",
                "productType": "waiting area sofa",
                "number_of_person": 3,
                "budget_min": 25_000_000,
                "budget_max": 10_000_000,
            },
            format="json",
        )
        self.assertEqual(400, response.status_code)

    def test_saved_recommendation_can_be_retrieved_and_rated(self):
        create_response = self.client.post(
            reverse("recommendation-create"),
            {
                "person": "employee",
                "productType": "office chair",
                "number_of_person": 1,
                "budget": 12_000_000,
            },
            format="json",
        )
        request_id = create_response.data["request_id"]

        detail = self.client.get(reverse("recommendation-detail", args=(request_id,)))
        feedback = self.client.post(
            reverse("recommendation-feedback", args=(request_id,)),
            {"was_helpful": True, "comment": "مناسب بود"},
            format="json",
        )

        self.assertEqual(200, detail.status_code)
        self.assertEqual(5, len(detail.data["recommendations"]))
        self.assertEqual(200, feedback.status_code)
        self.assertTrue(RecommendationFeedback.objects.get().was_helpful)

    def test_product_list_is_paginated(self):
        response = self.client.get(reverse("product-list"), {"person": "manager"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(27, response.data["count"])

    def test_persian_web_interface_is_available(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "انتخاب هوشمند مبلمان اداری")
        self.assertContains(response, 'id="chat-form"')
        self.assertContains(response, 'id="chat-history"')

    def test_health_check_is_available(self):
        response = self.client.get(reverse("health-check"))
        self.assertEqual(200, response.status_code)
        self.assertEqual({"status": "ok"}, response.json())

    def test_openapi_schema_and_swagger_are_available(self):
        schema = self.client.get(reverse("api-schema"))
        docs = self.client.get(reverse("api-docs"))
        self.assertEqual(200, schema.status_code)
        self.assertEqual(200, docs.status_code)

    @patch("apps.recommendations.chat_service.ask_model")
    def test_chat_adapter_uses_the_same_recommendation_engine(self, ask_model):
        ask_model.return_value = """{
            "user_input": {
                "person": "manager",
                "productType": "office desk",
                "number_of_person": 1,
                "budget": 15000000,
                "budget_min": null,
                "budget_max": null,
                "style": "modern",
                "color": "white",
                "fabric_material": null,
                "body_material": null
            },
            "llm_response": "اطلاعات کامل شد.",
            "success": true
        }"""
        response = self.client.post(
            reverse("chat"),
            {"message": "یک میز مدیریتی مدرن سفید می‌خواهم"},
            format="json",
        )

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.data["success"])
        ids = [item["product"]["id"] for item in response.data["recommendations"]]
        self.assertEqual([2, 4, 39, 3, 5], ids)

    @patch("apps.recommendations.chat_service.ask_model")
    def test_chat_rejects_a_structurally_invalid_model_response(self, ask_model):
        ask_model.return_value = '{"success": false}'

        response = self.client.post(
            reverse("chat"),
            {"message": "یک صندلی می‌خواهم"},
            format="json",
        )

        self.assertEqual(502, response.status_code)
        self.assertEqual("invalid_model_response", response.data["code"])
        self.assertIn("قابل پردازش نبود", response.data["detail"])

    @patch("apps.recommendations.chat_service.ask_model")
    def test_chat_forwards_state_and_recent_history(self, ask_model):
        ask_model.return_value = """{
            "user_input": {
                "person": "manager",
                "productType": "office desk",
                "number_of_person": null,
                "budget": null,
                "budget_min": null,
                "budget_max": null,
                "style": null,
                "color": null,
                "fabric_material": null,
                "body_material": null
            },
            "llm_response": "لطفاً بودجه را هم بفرمایید.",
            "success": false
        }"""
        history = [{"role": "assistant", "content": "چه نوع محصولی می‌خواهید؟"}]
        response = self.client.post(
            reverse("chat"),
            {
                "message": "برای مدیر است",
                "state": {"productType": "office desk"},
                "history": history,
            },
            format="json",
        )

        sent_context = json.loads(ask_model.call_args.args[1])
        self.assertEqual(200, response.status_code)
        self.assertEqual({"productType": "office desk"}, sent_context["current_user_input"])
        self.assertEqual(history, sent_context["recent_history"])
        self.assertEqual("برای مدیر است", sent_context["latest_message"])
        self.assertEqual("manager", response.data["state"]["person"])

    @patch("apps.recommendations.views.collect_chat_turn")
    def test_chat_reports_missing_or_invalid_api_key_in_persian(self, collect_turn):
        collect_turn.side_effect = LLMConfigurationError("OPENAI_API_KEY is missing")

        response = self.client.post(
            reverse("chat"),
            {"message": "یک صندلی می‌خواهم"},
            format="json",
        )

        self.assertEqual(503, response.status_code)
        self.assertEqual("chat_api_key_error", response.data["code"])
        self.assertIn("کلید API", response.data["detail"])
