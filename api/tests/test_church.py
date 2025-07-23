# These tests use Django's test framework, which creates a temporary database for testing.
# All data created, updated, or deleted in these tests is isolated and does not affect your real database.
# After the tests finish, the test database is deleted automatically.

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from api.models import Church
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class ChurchAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_payload = {
            "name": "Test Church",
            "email": "test@church.com",
            "phone": "+14155552671",
            "website": "https://testchurch.com",
            "street_address": "123 Main St",
            "city": "Springfield",
            "state": "CA",
            "zipcode": "90210",
            "status": "active",
        }
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

    def test_create_church_success(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        response = self.client.post(
            "/api/churches/create/", self.valid_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Church.objects.count(), 1)
        self.assertEqual(Church.objects.get().name, "Test Church")

    def test_create_duplicate_church(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        # Create the first church
        self.client.post("/api/churches/create/", self.valid_payload, format="json")
        # Try to create a duplicate
        response = self.client.post(
            "/api/churches/create/", self.valid_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "A church with this name, city, and state already exists.",
            str(response.data),
        )

    def test_invalid_state(self):
        payload = self.valid_payload.copy()
        payload["state"] = "California"
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        response = self.client.post("/api/churches/create/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is not a valid choice", str(response.data))

    def test_invalid_phone(self):
        payload = self.valid_payload.copy()
        payload["phone"] = "123"
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        response = self.client.post("/api/churches/create/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid phone number.", str(response.data))

    def test_invalid_zipcode(self):
        payload = self.valid_payload.copy()
        payload["zipcode"] = "abcde"
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        response = self.client.post("/api/churches/create/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid US ZIP code.", str(response.data))

    def test_atomic_rollback_on_invalid_user(self):
        """Church and all users should rollback if any user is invalid"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)

        payload = self.valid_payload.copy()
        payload["users"] = [
            {
                "email": "validuser@church.org",
                "first_name": "Valid",
                "last_name": "User",
                "password": "Password123!",
                "groups": ["Admin"],
                "status": "active",
                "requires_password_change": False
            },
            {
                "email": "",  # Invalid: required field
                "first_name": "Missing",
                "last_name": "Email",
                "password": "Password123!",
                "groups": ["Member"],
                "status": "active",
                "requires_password_change": False
            }
        ]
        response = self.client.post("/api/churches/create/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data["users"][1])
        self.assertEqual(Church.objects.count(), 0)
        self.assertFalse(User.objects.filter(email="validuser@church.org").exists())
