from django.db import models

from recommendation.models.sofa_model import (
    BodyMaterial,
    Color,
    FabricMaterial,
    ProductType,
    Style,
    UserType,
)


def enum_choices(enum_class):
    return [(item.value, item.value) for item in enum_class]


class Product(models.Model):
    legacy_id = models.PositiveIntegerField(unique=True)
    audience = models.CharField(max_length=20, choices=enum_choices(UserType))
    product_type = models.CharField(max_length=40, choices=enum_choices(ProductType))
    number_of_person = models.PositiveIntegerField()
    budget = models.PositiveBigIntegerField()
    style = models.CharField(max_length=20, choices=enum_choices(Style))
    color = models.CharField(max_length=20, choices=enum_choices(Color))
    fabric_material = models.CharField(
        max_length=20,
        choices=enum_choices(FabricMaterial),
        blank=True,
        default=FabricMaterial.unknown.value,
    )
    body_material = models.CharField(
        max_length=20,
        choices=enum_choices(BodyMaterial),
        blank=True,
        default=BodyMaterial.unknown.value,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("legacy_id",)
        indexes = [
            models.Index(fields=("audience", "product_type", "is_active")),
        ]

    def __str__(self) -> str:
        return f"{self.legacy_id} - {self.audience} - {self.product_type}"
