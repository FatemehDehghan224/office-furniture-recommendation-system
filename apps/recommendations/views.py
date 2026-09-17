import logging

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from openai import APIStatusError, AuthenticationError

from apps.products.models import Product
from apps.recommendations.models import RecommendationFeedback, RecommendationRequest
from apps.recommendations.serializers import (
    ChatInputSerializer,
    FeedbackSerializer,
    ProductSerializer,
    RecommendationDetailOutputSerializer,
    RecommendationInputSerializer,
    RecommendationOutputSerializer,
)
from apps.recommendations.services import create_recommendation
from apps.recommendations.chat_service import InvalidModelResponse, collect_chat_turn
from recommendation.utils.llm_client import LLMConfigurationError


logger = logging.getLogger(__name__)


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        filters = {
            "person": "audience",
            "productType": "product_type",
            "style": "style",
            "color": "color",
        }
        for query_name, model_name in filters.items():
            value = self.request.query_params.get(query_name)
            if value:
                queryset = queryset.filter(**{model_name: value})
        return queryset


class RecommendationCreateView(APIView):
    @extend_schema(
        request=RecommendationInputSerializer,
        responses={201: RecommendationOutputSerializer},
        summary="Create furniture recommendations",
    )
    def post(self, request):
        serializer = RecommendationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        top_k = data.pop("top_k")
        request_record, recommendations = create_recommendation(data, top_k=top_k)

        return Response(
            {
                "request_id": request_record.public_id,
                "count": len(recommendations),
                "recommendations": [
                    {
                        "rank": item.rank,
                        "score": item.score,
                        "price_difference": item.price_difference,
                        "product": ProductSerializer(item.product).data,
                    }
                    for item in recommendations
                ],
            },
            status=status.HTTP_201_CREATED,
        )


class RecommendationDetailView(APIView):
    @extend_schema(
        responses={200: RecommendationDetailOutputSerializer},
        summary="Retrieve a saved recommendation request",
    )
    def get(self, _request, public_id):
        request_record = get_object_or_404(
            RecommendationRequest.objects.prefetch_related("results__product"),
            public_id=public_id,
        )
        return Response(
            {
                "request_id": request_record.public_id,
                "created_at": request_record.created_at,
                "recommendations": [
                    {
                        "rank": result.rank,
                        "score": result.score,
                        "price_difference": result.price_difference,
                        "product": ProductSerializer(result.product).data,
                    }
                    for result in request_record.results.all()
                ],
            }
        )


class RecommendationFeedbackView(APIView):
    @extend_schema(
        request=FeedbackSerializer,
        responses={200: FeedbackSerializer},
        summary="Create or update recommendation feedback",
    )
    def post(self, request, public_id):
        request_record = get_object_or_404(RecommendationRequest, public_id=public_id)
        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feedback, _created = RecommendationFeedback.objects.update_or_create(
            request=request_record,
            defaults=serializer.validated_data,
        )
        return Response(FeedbackSerializer(feedback).data, status=status.HTTP_200_OK)


class ChatView(APIView):
    """Stateless conversational adapter; recommendation decisions remain deterministic."""

    @extend_schema(
        request=ChatInputSerializer,
        responses={200: OpenApiTypes.OBJECT},
        summary="Collect recommendation requirements from Persian chat",
    )
    def post(self, request):
        serializer = ChatInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            parsed = collect_chat_turn(**serializer.validated_data)
        except (LLMConfigurationError, AuthenticationError):
            return Response(
                {
                    "code": "chat_api_key_error",
                    "detail": "کلید API گفت‌وگو تنظیم نشده یا معتبر نیست. لطفاً تنظیمات سرویس را بررسی کنید.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except InvalidModelResponse:
            return Response(
                {
                    "code": "invalid_model_response",
                    "detail": "پاسخ مدل قابل پردازش نبود؛ لطفاً دوباره تلاش کنید.",
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except APIStatusError as error:
            if error.status_code in (401, 403):
                return Response(
                    {
                        "code": "chat_api_key_error",
                        "detail": "کلید API گفت‌وگو تنظیم نشده یا معتبر نیست. لطفاً تنظیمات سرویس را بررسی کنید.",
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            logger.exception("Conversational provider request failed")
            return Response(
                {"detail": "سرویس گفتگو موقتاً در دسترس نیست."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception:
            logger.exception("Conversational provider request failed")
            return Response(
                {"detail": "سرویس گفتگو موقتاً در دسترس نیست."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if "analysis_response" in parsed:
            return Response({"type": "analysis", "message": parsed["analysis_response"]})

        user_input = parsed.get("user_input") or {}
        response_data = {
            "type": "collection",
            "message": parsed.get("llm_response", ""),
            "success": bool(parsed.get("success", False)),
            "state": user_input,
        }
        if response_data["success"]:
            request_serializer = RecommendationInputSerializer(data=user_input)
            request_serializer.is_valid(raise_exception=True)
            normalized = dict(request_serializer.validated_data)
            top_k = normalized.pop("top_k")
            request_record, recommendations = create_recommendation(normalized, top_k=top_k)
            response_data.update(
                {
                    "request_id": request_record.public_id,
                    "recommendations": [
                        {
                            "rank": item.rank,
                            "score": item.score,
                            "price_difference": item.price_difference,
                            "product": ProductSerializer(item.product).data,
                        }
                        for item in recommendations
                    ],
                }
            )
        return Response(response_data)
