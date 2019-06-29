from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.test import APIClient

from core.models import Tag, UserModel

from recipe.serializers import TagSerializer

TAGS_URL = reverse("recipe:tag-list")


class PublicTagsApiTests(TestCase):
    """Test that the publicly available tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving tags"""
        res: Response = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    """Test the authorized usage of tags API"""

    def setUp(self):
        self.user: UserModel = get_user_model().objects.create_user(
            "test@example", "password123"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags"""
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Dessert")

        res: Response = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by("name")
        serializered_tags: ModelSerializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializered_tags.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are for the current authenticated user only"""
        another_user = get_user_model().objects.create_user(
            "another@example.com", "passwordanother"
        )
        Tag.objects.create(user=another_user, name="Chinese")
        tag: Tag = Tag.objects.create(user=self.user, name="Japanese")

        res: Response = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0].get("name"), tag.name)

    def test_create_tag_successful(self):
        """Test creating a new tag"""
        payload = {"name": "Test tag"}
        self.client.post(TAGS_URL, payload)

        tag_exists = Tag.objects.filter(
            user=self.user, name=payload.get("name")
        ).exists()

        self.assertTrue(tag_exists)

    def test_create_tag_invalid(self):
        """Test creating a new tag with invalid payload"""
        invalid_payload = {"name": ""}
        res: Response = self.client.post(TAGS_URL, invalid_payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
