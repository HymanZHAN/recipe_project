from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField

from core.models import Tag, Ingredient, Recipe


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


class RecipeSerializer(ModelSerializer):
    """Serializer for the recipe objects."""

    ingredients = PrimaryKeyRelatedField(many=True, queryset=Ingredient.objects.all())
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())

    class Meta:
        model = Recipe
        fields = (
            "id",
            "user",
            "title",
            "time_minutes",
            "price",
            "link",
            "ingredients",
            "tags",
        )
        read_only_fields = ("id",)
