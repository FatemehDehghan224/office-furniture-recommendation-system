import uuid

from django.db import models

from apps.products.models import Product, enum_choices
from recommendation.models.sofa_model import (
    BodyMaterial,
    Color,
    FabricMaterial,
    ProductType,
    Style,
    UserType,
)


class RecommendationRequest(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    person = models.CharField(max_length=20, choices=enum_choices(UserType))
    product_type = models.CharField(max_length=40, choices=enum_choices(ProductType))
    number_of_person = models.PositiveIntegerField()
    budget = models.PositiveBigIntegerField(null=True, blank=True)
    budget_min = models.PositiveBigIntegerField(null=True, blank=True)
    budget_max = models.PositiveBigIntegerField(null=True, blank=True)
    style = models.CharField(max_length=20, choices=enum_choices(Style), null=True, blank=True)
    color = models.CharField(max_length=20, choices=enum_choices(Color), null=True, blank=True)
    fabric_material = models.CharField(
        max_length=20,
        choices=enum_choices(FabricMaterial),
        null=True,
        blank=True,
    )
    body_material = models.CharField(
        max_length=20,
        choices=enum_choices(BodyMaterial),
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class RecommendationResult(models.Model):
    request = models.ForeignKey(
        RecommendationRequest,
        on_delete=models.CASCADE,
        related_name="results",
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    rank = models.PositiveSmallIntegerField()
    score = models.SmallIntegerField()
    price_difference = models.FloatField()

    class Meta:
        ordering = ("rank",)
        constraints = [
            models.UniqueConstraint(fields=("request", "rank"), name="unique_result_rank"),
            models.UniqueConstraint(fields=("request", "product"), name="unique_result_product"),
        ]


class RecommendationFeedback(models.Model):
    request = models.OneToOneField(
        RecommendationRequest,
        on_delete=models.CASCADE,
        related_name="feedback",
    )
    was_helpful = models.BooleanField()
    comment = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
