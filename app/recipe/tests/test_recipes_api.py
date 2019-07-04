import os
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe, Tag
from recipe.serializers import ModelSerializer, RecipeDetailSerializer, RecipeSerializer

RECIPES_URL = reverse("recipe:recipe-list")


def image_upload_url(recipe_id):
    """Return url for recipe image uploads"""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


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
    defaults = {"title": "Sample Recipe", "time_minutes": 10, "price": Decimal("4.99")}
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test the public available recipe API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is always required for this endpoint"""
        res: Response = self.client.get(RECIPES_URL)

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
        """Test that user can retrieve recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res: Response = self.client.get(RECIPES_URL)

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

        res: Response = self.client.get(RECIPES_URL)

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

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {"title": "Test recipe", "time_minutes": 30, "price": Decimal("5.55")}
        res: Response = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        for key in payload:
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        tag1 = sample_tag(user=self.user, name="Tag 1")
        tag2 = sample_tag(user=self.user, name="Tag 2")
        payload = {
            "title": "Test recipe with two tags",
            "tags": [tag1.id, tag2.id],
            "time_minutes": 30,
            "price": 19.78,
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data["id"])
        tags = recipe.tags.all()

        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating recipe with ingredients"""
        ingredient_one = sample_ingredient(user=self.user, name="Ingredient 1")
        ingredient_two = sample_ingredient(user=self.user, name="Ingredient 2")
        payload = {
            "title": "Test recipe with ingredients",
            "ingredients": [ingredient_one.id, ingredient_two.id],
            "time_minutes": 45,
            "price": 25.98,
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data["id"])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient_one, ingredients)
        self.assertIn(ingredient_two, ingredients)

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        recipe: Recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name="Curry")

        payload = {"title": "Chicken tikka", "tags": [new_tag.id]}

        url = recipe_detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload.get("title"))
        self.assertEqual(recipe.tags.count(), 1)
        self.assertIn(new_tag, recipe.tags.all())

    def test_full_update_recipe(self):
        """Test updating a recipe with PUT"""
        recipe: Recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {"title": "Chow Mein", "time_minutes": 15, "price": Decimal("6.98")}

        url = recipe_detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload.get("title"))
        self.assertEqual(recipe.time_minutes, payload.get("time_minutes"))
        self.assertEqual(recipe.price, payload.get("price"))

        self.assertEqual(recipe.tags.count(), 0)


class RecipeImageUploadTests(TestCase):
    """ Test uploading image to a specific recipe"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@example.com", "password123"
        )
        self.client.force_authenticate(self.user)
        self.recipe: Recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test upload an image to a recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res: Response = self.client.post(url, {"image": ntf}, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        res: Response = self.client.post(
            url, {"image": "This is a string!"}, format="multipart"
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipes_by_tags(self):
        """Test returning recipes with specific tags"""
        recipe_one: Recipe = sample_recipe(user=self.user, title="Thai Curry")
        recipe_two: Recipe = sample_recipe(user=self.user, title="Orange Chicken")

        tag_one: Tag = sample_tag(user=self.user, name="Thai")
        tag_two: Tag = sample_tag(user=self.user, name="American")

        recipe_one.tags.add(tag_one)
        recipe_two.tags.add(tag_two)

        recipe_three = sample_recipe(user=self.user, title="Fish and Chips")

        res: Response = self.client.get(
            RECIPES_URL, {"tags": f"{tag_one.id}, {tag_two.id}"}
        )

        serializer_one = RecipeSerializer(recipe_one)
        serializer_two = RecipeSerializer(recipe_two)
        serializer_three = RecipeSerializer(recipe_three)

        self.assertIn(serializer_one.data, res.data)
        self.assertIn(serializer_two.data, res.data)
        self.assertNotIn(serializer_three.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """Test returning recipes with specific ingredients"""

        recipe_one = sample_recipe(user=self.user, title="Posh beans on toast")
        recipe_two = sample_recipe(user=self.user, title="Chicken cacciatore")
        ingredient_one = sample_ingredient(user=self.user, name="Feta cheese")
        ingredient_two = sample_ingredient(user=self.user, name="Chicken")
        recipe_one.ingredients.add(ingredient_one)
        recipe_two.ingredients.add(ingredient_two)
        recipe_three = sample_recipe(user=self.user, title="Steak and mushrooms")

        res = self.client.get(
            RECIPES_URL, {"ingredients": f"{ingredient_one.id},{ingredient_two.id}"}
        )

        serializer1 = RecipeSerializer(recipe_one)
        serializer2 = RecipeSerializer(recipe_two)
        serializer3 = RecipeSerializer(recipe_three)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
