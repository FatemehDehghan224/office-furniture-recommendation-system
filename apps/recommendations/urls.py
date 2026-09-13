from django.urls import path

from apps.recommendations.views import (
    ChatView,
    ProductListView,
    RecommendationCreateView,
    RecommendationDetailView,
    RecommendationFeedbackView,
)


urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("recommendations/", RecommendationCreateView.as_view(), name="recommendation-create"),
    path(
        "recommendation-requests/<uuid:public_id>/",
        RecommendationDetailView.as_view(),
        name="recommendation-detail",
    ),
    path(
        "recommendation-requests/<uuid:public_id>/feedback/",
        RecommendationFeedbackView.as_view(),
        name="recommendation-feedback",
    ),
]
