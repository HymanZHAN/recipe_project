from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from core.models import Ingredient, UserModel, Recipe
from recipe.serializers import IngredientSerializer, ModelSerializer

INGREDIENT_URL = reverse("recipe:ingredient-list")


class PublicIngredientApiTest(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is always required for this endpoint"""
        res: Response = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTest(TestCase):
    """Test the authorized usage of ingredient API"""

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
        ingredients = Ingredient.objects.all().order_by("name")
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

    def test_create_ingredient_successful(self):
        """Test that creating a new ingredient is successful"""
        payload = {"name": "Black Pepper"}
        self.client.post(INGREDIENT_URL, payload)

        new_ingredient_exists = Ingredient.objects.filter(
            user=self.user, name=payload.get("name")
        ).exists()

        self.assertTrue(new_ingredient_exists)

    def test_create_ingredient_invalid(self):
        """Test creating invalid ingredient fails"""
        invalid_payload = {"name": ""}
        res: Response = self.client.post(INGREDIENT_URL, invalid_payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipes(self):
        """Test filtering ingredients by those assigned to recipes"""
        ingredient_one = Ingredient.objects.create(user=self.user, name="Apples")
        ingredient_two = Ingredient.objects.create(user=self.user, name="Turkey")
        recipe = Recipe.objects.create(
            title="Apple crumble", time_minutes=5, price=10.00, user=self.user
        )
        recipe.ingredients.add(ingredient_one)

        res = self.client.get(INGREDIENT_URL, {"assigned_only": 1})

        serializer1 = IngredientSerializer(ingredient_one)
        serializer2 = IngredientSerializer(ingredient_two)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredient_assigned_unique(self):
        """Test filtering ingredients by assigned returns unique items"""
        ingredient = Ingredient.objects.create(user=self.user, name="Eggs")
        recipe_one = Recipe.objects.create(
            title="Eggs benedict", time_minutes=30, price=12.00, user=self.user
        )
        recipe_one.ingredients.add(ingredient)
        recipe_two = Recipe.objects.create(
            title="Green eggs on toast", time_minutes=20, price=5.00, user=self.user
        )
        recipe_two.ingredients.add(ingredient)

        res: Response = self.client.get(INGREDIENT_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
