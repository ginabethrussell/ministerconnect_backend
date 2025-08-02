from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import InviteCode


User = get_user_model()


class InviteCodeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="inviteuser@church.org",
            email="inviteuser@church.org",
            password="securepassword",
            name="Invite User",
            status="active",
            is_active=True,
        )

        # Add the user to the Admin group
        admin_group = Group.objects.get_or_create(name="Admin")[0]
        self.user.groups.set([admin_group])

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_create_invite_code_success(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        payload = {
            "code": "CHURCH2024",
            "event": "Spring 2024 Church Registration",
            "expires_at": "2024-12-31T23:59:59Z",
        }
        response = self.client.post("/api/invite-codes/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["code"], "CHURCH2024")
        self.assertEqual(response.data["event"], "Spring 2024 Church Registration")
        self.assertEqual(response.data["status"], "active")
        self.assertEqual(response.data["created_by"], self.user.id)
        self.assertEqual(response.data["created_by_name"], self.user.name)

    def test_create_invite_code_unauthenticated(self):
        payload = {
            "code": "CHURCH2025",
            "event": "Spring 2025 Church Registration",
            "expires_at": "2025-12-31T23:59:59Z",
        }
        response = self.client.post("/api/invite-codes/", payload, format="json")
        self.assertEqual(response.status_code, 401)

    def test_create_invite_code_missing_fields(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        payload = {
            "event": "Spring 2024 Church Registration"
            # Missing 'code' and 'expires_at'
        }
        response = self.client.post("/api/invite-codes/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("code", response.data)
        self.assertIn("expires_at", response.data)


class InviteCodeListAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="listuser@church.org",
            email="listuser@church.org",
            password="securepassword",
            name="List User",
            status="active",
            is_active=True,
        )

        # Add the user to the Admin group
        admin_group = Group.objects.get_or_create(name="Admin")[0]
        self.user.groups.set([admin_group])

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_get_invite_codes_success(self):
        # Create some invite codes
        InviteCode.objects.create(
            code="CODE1",
            event="Event 1",
            expires_at="2024-12-31T23:59:59Z",
            created_by=self.user,
        )
        InviteCode.objects.create(
            code="CODE2",
            event="Event 2",
            expires_at="2025-12-31T23:59:59Z",
            created_by=self.user,
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        response = self.client.get("/api/invite-codes/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 2)
        codes = [item["code"] for item in response.data["results"]]
        self.assertIn("CODE1", codes)
        self.assertIn("CODE2", codes)
        for item in response.data["results"]:
            self.assertEqual(item["created_by_name"], self.user.name)

    def test_get_invite_codes_unauthenticated(self):
        response = self.client.get("/api/invite-codes/")
        self.assertEqual(response.status_code, 401)

    def test_get_invite_codes_empty(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        response = self.client.get("/api/invite-codes/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])
        self.assertEqual(response.data["count"], 0)
