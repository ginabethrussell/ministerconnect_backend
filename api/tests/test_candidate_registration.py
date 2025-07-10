from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from api.models import InviteCode

User = get_user_model()


class CandidateRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.invite = InviteCode.objects.create(
            code="CANDIDATE2024",
            event="Spring 2024 Candidate Registration",
            status="active",
            used_count=0,
            expires_at="2024-12-31T23:59:59Z",
            created_by=User.objects.create_user(
                username="admin@church.org",
                email="admin@church.org",
                password="adminpass",
                name="Admin User",
                status="active",
                is_active=True,
            ),
        )
        Group.objects.get_or_create(name="Candidate")
        self.valid_payload = {
            "invite_code": "CANDIDATE2024",
            "email": "candidate@example.com",
            "password": "securepassword",
            "first_name": "Jane",
            "last_name": "Doe",
        }

    def test_candidate_registration_success(self):
        response = self.client.post(
            "/api/candidates/register/", self.valid_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="candidate@example.com").exists())
        user = User.objects.get(email="candidate@example.com")
        self.assertTrue(user.groups.filter(name="Candidate").exists())
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.name, "Jane Doe")
        invite = InviteCode.objects.get(code="CANDIDATE2024")
        self.assertEqual(invite.used_count, 1)

    def test_candidate_registration_invalid_invite_code(self):
        payload = self.valid_payload.copy()
        payload["invite_code"] = "INVALIDCODE"
        response = self.client.post("/api/candidates/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invite_code", response.data)

    def test_candidate_registration_inactive_invite_code(self):
        self.invite.status = "expired"
        self.invite.save()
        payload = self.valid_payload.copy()
        response = self.client.post("/api/candidates/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invite_code", response.data)

    def test_candidate_registration_duplicate_email(self):
        User.objects.create_user(
            username="candidate@example.com",
            email="candidate@example.com",
            password="securepassword",
            name="Jane Doe",
            status="active",
            is_active=True,
        )
        response = self.client.post(
            "/api/candidates/register/", self.valid_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_candidate_registration_missing_fields(self):
        payload = {
            "invite_code": "CANDIDATE2024",
            "email": "missingfields@example.com",
            # Missing password, first_name, last_name
        }
        response = self.client.post("/api/candidates/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertIn("first_name", response.data)
        self.assertIn("last_name", response.data)
