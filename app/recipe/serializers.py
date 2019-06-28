from rest_framework.serializers import ModelSerializer

from core.models import Tag, Ingredient


class TagSerializer(ModelSerializer):
    """Serializer for the tag objects."""

    class Meta:
        model = Tag
        fields = ("id", "name")
        read_only_fields = ("id",)


class IngredientSerializer(ModelSerializer):
    """Serializer for the ingredient objects."""

    class Meta:
        model = Ingredient
        fields = ("id", "name")
        read_only_fields = ("id",)
