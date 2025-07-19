from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import InviteCode

User = get_user_model()


class ProfileAPITests(TestCase):
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

    def test_candidate_registration_duplicate_email(self):
        # First registration with a unique email
        payload = {
            "invite_code": self.invite_code.code,
            "email": "unique_candidate@example.com",  # Use a unique email
            "password": "securepassword",
            "first_name": "Test",
            "last_name": "Candidate",
        }
        response1 = self.client.post(
            "/api/candidates/register/", payload, format="json"
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second registration with the same email
        response2 = self.client.post(
            "/api/candidates/register/", payload, format="json"
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response2.data)

    def test_candidate_registration_success(self):
        payload = {
            "invite_code": self.invite_code.code,  # Use code string
            "email": "newcandidate@example.com",
            "password": "newsecurepassword",
            "first_name": "New",
            "last_name": "TestCandidate",
        }
        response = self.client.post("/api/candidates/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=payload["email"]).exists())

    def test_profile_me_exists_after_candidate_registration(self):
        # Register a new candidate
        payload = {
            "invite_code": self.invite_code.code,
            "email": "profiletest@example.com",
            "password": "securepassword",
            "first_name": "Profile",
            "last_name": "Test",
        }
        response = self.client.post("/api/candidates/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Log in as the new candidate to get a token
        login_payload = {
            "email": "profiletest@example.com",
            "password": "securepassword",
        }
        login_response = self.client.post("/api/token/", login_payload, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data["access"]
        # Use the new token for the profile check
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + access_token)
        profile_response = self.client.get("/api/profile/me/")
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data["status"], "draft")
        self.assertEqual(
            profile_response.data["user"],
            User.objects.get(email="profiletest@example.com").id,
        )
