from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.http import HttpResponse

from ..models import UserModel


class AdminSiteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com", password="passwordadmin"
        )
        self.client.force_login(self.admin_user)
        self.user: UserModel = get_user_model().objects.create_user(
            email="test@example.com", password="password123", name="TEST NORMAL USERNAME"
        )

    def test_users_listed(self):
        """Test that users are listed on user page"""
        url = reverse("admin:core_usermodel_changelist")
        res: HttpResponse = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_user_change_page(self):
        """Test that user edit page works"""
        url = reverse("admin:core_usermodel_change", args=[self.user.id])
        res: HttpResponse = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        url = reverse("admin:core_usermodel_add")
        res: HttpResponse = self.client.get(url)

        self.assertEqual(res.status_code, 200)
