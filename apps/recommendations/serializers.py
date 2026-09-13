from rest_framework import serializers

from apps.products.models import Product
from apps.recommendations.models import RecommendationFeedback
from recommendation.models.sofa_model import (
    BodyMaterial,
    Color,
    FabricMaterial,
    ProductType,
    Style,
    UserType,
)


def values(enum_class):
    return [item.value for item in enum_class]


class RecommendationInputSerializer(serializers.Serializer):
    person = serializers.ChoiceField(choices=values(UserType))
    productType = serializers.ChoiceField(choices=values(ProductType))
    number_of_person = serializers.IntegerField(min_value=1)
    budget = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    budget_min = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    budget_max = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    style = serializers.ChoiceField(choices=values(Style), required=False, allow_null=True)
    color = serializers.ChoiceField(choices=values(Color), required=False, allow_null=True)
    fabric_material = serializers.ChoiceField(
        choices=values(FabricMaterial), required=False, allow_null=True, allow_blank=True
    )
    body_material = serializers.ChoiceField(
        choices=values(BodyMaterial), required=False, allow_null=True, allow_blank=True
    )
    top_k = serializers.IntegerField(min_value=1, max_value=20, default=5, write_only=True)

    def validate(self, attrs):
        minimum = attrs.get("budget_min")
        maximum = attrs.get("budget_max")
        if (minimum is None) != (maximum is None):
            raise serializers.ValidationError(
                "budget_min و budget_max باید با هم ارسال شوند."
            )
        if minimum is not None and minimum > maximum:
            raise serializers.ValidationError("budget_min نمی‌تواند از budget_max بیشتر باشد.")
        if attrs.get("budget") is not None and minimum is not None:
            raise serializers.ValidationError(
                "فقط یکی از budget یا بازهٔ budget_min/budget_max را ارسال کنید."
            )
        return attrs


class ProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="legacy_id", read_only=True)
    person = serializers.CharField(source="audience", read_only=True)
    productType = serializers.CharField(source="product_type", read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "person",
            "productType",
            "number_of_person",
            "budget",
            "style",
            "color",
            "fabric_material",
            "body_material",
        )


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationFeedback
        fields = ("was_helpful", "comment")


class ChatHistoryItemSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=("user", "assistant"))
    content = serializers.CharField(max_length=2_000)


class ChatInputSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2_000)
    state = serializers.DictField(required=False, default=dict)
    history = ChatHistoryItemSerializer(many=True, required=False, default=list)

    def validate_history(self, value):
        if len(value) > 20:
            raise serializers.ValidationError("حداکثر ۲۰ پیام اخیر قابل ارسال است.")
        return value


class RecommendationItemSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    score = serializers.IntegerField()
    price_difference = serializers.FloatField()
    product = ProductSerializer()


class RecommendationOutputSerializer(serializers.Serializer):
    request_id = serializers.UUIDField()
    count = serializers.IntegerField()
    recommendations = RecommendationItemSerializer(many=True)


class RecommendationDetailOutputSerializer(serializers.Serializer):
    request_id = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    recommendations = RecommendationItemSerializer(many=True)
