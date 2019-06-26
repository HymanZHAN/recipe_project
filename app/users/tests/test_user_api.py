from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from core.models import UserModel

CREATE_USER_URL = reverse("users:create")
TOKEN_URL = reverse("users:token")
ME_URL = reverse("users:me")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        payload = {
            "email": "test@example.com",
            "password": "password",
            "name": "Test name",
        }
        res: Response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user: UserModel = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_exists(self):
        """Test creating a user that already exists fails"""
        payload = {
            "email": "test@example.com",
            "password": "password",
            "name": "Test name",
        }
        create_user(**payload)

        res: Response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that the password must be more than 5 characters"""
        payload = {"email": "test@example.com", "password": "pw"}
        res: Response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = (
            get_user_model().objects.filter(email=payload.get("email")).exists()
        )
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a token is created for a user"""
        payload = {"email": "test@example.com", "password": "password123"}
        create_user(**payload)
        res: Response = self.client.post(TOKEN_URL, payload)

        self.assertIn("token", res.data)
        self.assertTrue(res.status_code, status.HTTP_200_OK)

    def test_create_token_for_invalid_credentials(self):
        """Test that token is not created for invalid credentials."""
        correct_user_info = {"email": "test@example.com", "password": "password123"}
        create_user(**correct_user_info)
        invalid_user_info = {"email": "test@example.com", "password": "wrongpass"}
        res: Response = self.client.post(TOKEN_URL, invalid_user_info)

        self.assertNotIn("token", res.data)
        self.assertTrue(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_for_nonexistent_user(self):
        """Test that token is not created for nonexistent user."""
        user_info = {"email": "test@example.com", "password": "password123"}
        res: Response = self.client.post(TOKEN_URL, user_info)

        self.assertNotIn("token", res.data)
        self.assertTrue(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_fields(self):
        """Test that token is not created for incomplete info"""
        user_info = {"email": "test@example.com", "password": "password123"}
        create_user(**user_info)
        incomplete_user_info = {"email": "test@example.com", "password": ""}
        res: Response = self.client.post(TOKEN_URL, incomplete_user_info)

        self.assertNotIn("token", res.data)
        self.assertTrue(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for users"""
        res: Response = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTest(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        self.user: UserModel = create_user(
            email="test@example.com", password="password123", name="test user"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        res: Response = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {"name": self.user.name, "email": self.user.email})

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed not allowed on the ME_URL"""
        res: Response = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test that updating user profile is successful for authenticated user"""
        new_user_info = {"name": "new name", "password": "newpassword"}
        res: Response = self.client.patch(ME_URL, new_user_info)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, new_user_info.get("name"))
        self.assertTrue(self.user.check_password(new_user_info.get("password")))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
