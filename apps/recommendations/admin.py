from django.contrib import admin

from apps.recommendations.models import (
    RecommendationFeedback,
    RecommendationRequest,
    RecommendationResult,
)


class RecommendationResultInline(admin.TabularInline):
    model = RecommendationResult
    extra = 0
    readonly_fields = ("product", "rank", "score", "price_difference")


@admin.register(RecommendationRequest)
class RecommendationRequestAdmin(admin.ModelAdmin):
    list_display = ("public_id", "person", "product_type", "created_at")
    list_filter = ("person", "product_type", "created_at")
    readonly_fields = ("public_id", "created_at")
    inlines = (RecommendationResultInline,)


admin.site.register(RecommendationFeedback)
