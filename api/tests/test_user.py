# These tests use Django's test framework, which creates a temporary database for testing.
# All data created, updated, or deleted in these tests is isolated and does not affect your real database.
# After the tests finish, the test database is deleted automatically.

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from api.models import Church
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.church = Church.objects.create(
            name="Test Church",
            email="test@church.com",
            phone="+14155552671",
            website="https://testchurch.com",
            street_address="123 Main St",
            city="Springfield",
            state="CA",
            zipcode="90210",
            status="active",
        )
        # Create a user and get a token
        self.user = User.objects.create_user(
            email="authuser@church.org",
            username="authuser@church.org",
            password="securepassword",
            name="Auth User",
            status="active",
        )
        # Get JWT token for the user
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        Group.objects.get_or_create(name="Church User")
        self.valid_payload = {
            "email": "user@church.org",
            "username": "user@church.org",
            "name": "Jane Doe",
            "password": "securepassword",
            "groups": ["Church User"],
            "church_id": self.church.id,
            "status": "pending",
            "requires_password_change": True,
        }

    def test_create_user_success(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        response = self.client.post(
            "/api/users/create/", self.valid_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertTrue(User.objects.filter(email="user@church.org").exists())

    def test_create_user_bad_request(self):
        payload = self.valid_payload.copy()
        del payload["email"]  # Remove required field
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        response = self.client.post("/api/users/create/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_create_user_church_not_found(self):
        payload = self.valid_payload.copy()
        payload["church_id"] = 9999  # Non-existent church ID
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        response = self.client.post("/api/users/create/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("church_id", response.data)

    def test_create_user_duplicate(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        # Create the user once
        self.client.post("/api/users/create/", self.valid_payload, format="json")
        # Try to create the same user again
        response = self.client.post(
            "/api/users/create/", self.valid_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_user_me_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        response = self.client.get("/api/user/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["id"], self.user.id)
        self.assertEqual(data["email"], self.user.email)
        self.assertEqual(data["name"], self.user.name)
        self.assertEqual(data["status"], self.user.status)
        self.assertIn("groups", data)
        self.assertIsInstance(data["groups"], list)

    def test_user_me_unauthenticated(self):
        response = self.client.get("/api/user/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
