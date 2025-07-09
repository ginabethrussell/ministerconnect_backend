# These tests use Django's test framework, which creates a temporary database for testing.
# All data created, updated, or deleted in these tests is isolated and does not affect your real database.
# After the tests finish, the test database is deleted automatically.

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from api.models import Church
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AuthenticatedEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a user and get a token
        self.user = User.objects.create_user(
            email="authuser@church.org",
            username="authuser@church.org",
            password="securepassword",
            name="Auth User",
            status="active",
        )
        self.church = Church.objects.create(
            name="Auth Church",
            email="auth@church.com",
            phone="+14155552671",
            website="https://authchurch.com",
            street_address="123 Main St",
            city="Springfield",
            state="CA",
            zipcode="90210",
            status="active",
        )
        # Get JWT token for the user
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.church_payload = {
            "name": "Protected Church",
            "email": "protected@church.com",
            "phone": "+14155552671",
            "website": "https://protectedchurch.com",
            "street_address": "456 Main St",
            "city": "Springfield",
            "state": "CA",
            "zipcode": "90210",
            "status": "active",
        }

    def test_protected_endpoint_requires_auth(self):
        # Try without authentication
        response = self.client.post(
            "/api/churches/create/", self.church_payload, format="json"
        )
        self.assertEqual(response.status_code, 401)  # Unauthorized

    def test_protected_endpoint_with_auth(self):
        # Set the Authorization header
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        response = self.client.post(
            "/api/churches/create/", self.church_payload, format="json"
        )
        self.assertIn(response.status_code, [200, 201])  # Created or OK


class JWTAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="jwtuser@church.org",
            email="jwtuser@church.org",
            password="securepassword",
            name="JWT User",
            status="active",
            is_active=True,
        )

    def test_token_obtain(self):
        response = self.client.post(
            "/api/token/",
            {"email": "jwtuser@church.org", "password": "securepassword"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.access_token = response.data["access"]
        self.refresh_token = response.data["refresh"]

    def test_token_refresh(self):
        # First, obtain a refresh token
        response = self.client.post(
            "/api/token/",
            {"email": "jwtuser@church.org", "password": "securepassword"},
            format="json",
        )
        refresh_token = response.data["refresh"]
        # Now, refresh the access token
        response = self.client.post(
            "/api/token/refresh/", {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
