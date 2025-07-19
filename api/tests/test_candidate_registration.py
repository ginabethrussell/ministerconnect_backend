from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from api.models import InviteCode
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class CandidateRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a user to use as the creator of the invite code
        creator = User.objects.create_user(
            email="creator@example.com",
            username="creator@example.com",
            password="password",
            name="Creator User",
            status="active",
        )
        self.invite_code = InviteCode.objects.create(
            code="CANDIDATE2024",
            event="Spring 2024 Registration",
            used_count=0,
            status="active",
            created_by=creator,
            expires_at="2099-12-31T23:59:59Z",
        )
        self.user = User.objects.create_user(
            email="candidate@example.com",
            username="candidate@example.com",
            password="securepassword",
            name="Test Candidate",
            status="active",
            invite_code=self.invite_code,
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        Group.objects.get_or_create(name="Candidate")
        self.valid_payload = {
            "invite_code": self.invite_code.code,  # Use the ID, not the code string
            "email": "candidate1@example.com",
            "password": "securepassword",
            "first_name": "Jane",
            "last_name": "Doe",
        }

    def test_candidate_registration_success(self):
        response = self.client.post(
            "/api/candidates/register/", self.valid_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="candidate1@example.com").exists())
        user = User.objects.get(email="candidate1@example.com")
        self.assertTrue(user.groups.filter(name="Candidate").exists())
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.name, "Jane Doe")
        invite = InviteCode.objects.get(code="CANDIDATE2024")
        self.assertEqual(invite.used_count, 1)

    def test_candidate_registration_invalid_invite_code(self):
        payload = self.valid_payload.copy()
        payload["invite_code"] = 99999  # Use a non-existent ID
        response = self.client.post("/api/candidates/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invite_code", response.data)

    def test_candidate_registration_inactive_invite_code(self):
        self.invite_code.status = "expired"
        self.invite_code.save()
        payload = self.valid_payload.copy()
        response = self.client.post("/api/candidates/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invite_code", response.data)

    def test_candidate_registration_duplicate_email(self):
        # First registration
        response1 = self.client.post(
            "/api/candidates/register/", self.valid_payload, format="json"
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        # Second registration with same email
        response2 = self.client.post(
            "/api/candidates/register/", self.valid_payload, format="json"
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response2.data)

    def test_candidate_registration_missing_fields(self):
        payload = {
            "invite_code": self.invite_code.id,
            "email": "missingfields@example.com",
            # Missing password, first_name, last_name
        }
        response = self.client.post("/api/candidates/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertIn("first_name", response.data)
        self.assertIn("last_name", response.data)
