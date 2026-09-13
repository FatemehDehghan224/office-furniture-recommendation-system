from django.contrib import admin

from apps.products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "legacy_id",
        "audience",
        "product_type",
        "budget",
        "style",
        "color",
        "is_active",
    )
    list_filter = ("audience", "product_type", "style", "color", "is_active")
    search_fields = ("=legacy_id",)
    ordering = ("legacy_id",)
