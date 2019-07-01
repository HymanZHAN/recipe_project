from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from core.models import Recipe, Ingredient, Tag
from recipe.serializers import RecipeSerializer, ModelSerializer, RecipeDetailSerializer

RECIPE_URL = reverse("recipe:recipe-list")


def recipe_detail_url(recipe_id):
    """Return recipe detail url"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def sample_tag(user, name="Main Course"):
    """Create and return a sample tag"""

    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name="Cinnamon"):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""

    defaults = {"title": "Sample Recipe", "time_minutes": 10, "price": 5.00}

    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test the public available recipe API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is always required for this endpoint"""
        res: Response = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test the authorized usage of recipe API"""

    def setUp(self):
        self.client = APIClient()

        self.user = get_user_model().objects.create_user(
            "test@example.com", "password123"
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipe(self):
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res: Response = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer: ModelSerializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_current_user(self):
        """Test that retrieved recipes are limited for the current authorized user only"""
        another_user = get_user_model().objects.create_user(
            "another@example.com", "anotherpassword"
        )

        sample_recipe(user=self.user)
        sample_recipe(user=another_user)

        res: Response = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertTrue(res.status_code, status.HTTP_200_OK)
        self.assertTrue(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe: Recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = recipe_detail_url(recipe.id)
        res: Response = self.client.get(url)

        serializer: ModelSerializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)
