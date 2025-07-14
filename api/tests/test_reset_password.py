from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class ResetPasswordAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="resetuser@example.com",
            username="resetuser@example.com",
            password="oldpassword123",
            name="Reset User",
            status="active",
            requires_password_change=True,
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)

    def test_reset_password_success(self):
        payload = {
            "temporary_password": "oldpassword123",
            "new_password": "newsecurepassword456",
        }
        response = self.client.post("/api/reset-password/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newsecurepassword456"))
        self.assertFalse(self.user.requires_password_change)

    def test_reset_password_invalid_temporary_password(self):
        payload = {
            "temporary_password": "wrongpassword",
            "new_password": "newsecurepassword456",
        }
        response = self.client.post("/api/reset-password/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("oldpassword123"))
        self.assertTrue(self.user.requires_password_change)

    def test_reset_password_too_short(self):
        payload = {"temporary_password": "oldpassword123", "new_password": "short"}
        response = self.client.post("/api/reset-password/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("oldpassword123"))
        self.assertTrue(self.user.requires_password_change)
