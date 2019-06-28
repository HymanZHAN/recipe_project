from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from core.models import Ingredient, UserModel
from recipe.serializers import IngredientSerializer, ModelSerializer

INGREDIENT_URL = reverse("recipe:ingredient-list")


class PublicIngredientApiTest(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that lgoin is always required for this endpoint"""
        res: Response = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTest(TestCase):
    """Test the authorized usage of ingredient api"""

    def setUp(self):
        self.user: UserModel = get_user_model().objects.create_user(
            email="test@example.com", password="password123"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieve a list of ingredients"""
        Ingredient.objects.create(user=self.user, name="Carrot")
        Ingredient.objects.create(user=self.user, name="Beef")
        Ingredient.objects.create(user=self.user, name="Celery")

        res: Response = self.client.get(INGREDIENT_URL)
        ingredients = Ingredient.objects.all().order_by("-name")
        serializered_ingredients: ModelSerializer = IngredientSerializer(
            ingredients, many=True
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializered_ingredients.data)

    def test_ingredients_limited_to_user(self):
        """Test that ingredients returned are for the current authenticated user only"""
        another_user = get_user_model().objects.create_user(
            "another@example.com", "passwordanother"
        )
        Ingredient.objects.create(user=another_user, name="Beef")
        ingredient: Ingredient = Ingredient.objects.create(
            user=self.user, name="Chicken"
        )

        res: Response = self.client.get(INGREDIENT_URL)

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0].get("name"), ingredient.name)
