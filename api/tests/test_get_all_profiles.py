from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import Profile, InviteCode

User = get_user_model()


class ProfileListAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create groups
        self.admin_group = Group.objects.create(name="Admin")
        self.church_group = Group.objects.create(name="Church User")

        # Create a user who can create invite codes
        creator = User.objects.create_user(
            email="creator@example.com",
            username="creator@example.com",
            password="password",
            name="Creator User",
            status="active",
        )

        # Invite code used by profiles
        self.invite_code = InviteCode.objects.create(
            code="CANDIDATE2024",
            event="Spring 2024 Registration",
            used_count=0,
            status="active",
            created_by=creator,
            expires_at="2099-12-31T23:59:59Z",
        )

        # Authorized admin user
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin@example.com",
            password="securepassword",
            name="Admin User",
            status="active",
        )
        self.admin_user.groups.add(self.admin_group)
        refresh = RefreshToken.for_user(self.admin_user)
        self.admin_token = str(refresh.access_token)

        # Create multiple profiles for pagination
        for i in range(51):
            user = User.objects.create_user(
                email=f"user{i}@example.com",
                username=f"user{i}@example.com",
                password="testpassword",
                name=f"User {i}",
                status="active",
            )
            Profile.objects.create(
                user=user,
                invite_code=self.invite_code,
                city="City",
                state="ST",
                status="approved" if i % 2 == 0 else "pending",
            )

    def test_get_all_profiles_success_with_pagination(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_token)
        response = self.client.get("/api/profiles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 50)  # default page size
        self.assertEqual(response.data["count"], 51)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_get_profiles_filtered_by_status(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_token)
        response = self.client.get("/api/profiles/?status=pending")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for profile in response.data["results"]:
            self.assertEqual(profile["status"], "pending")

    def test_get_profiles_unauthenticated(self):
        self.client.credentials()  # no token
        response = self.client.get("/api/profiles/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profiles_authenticated_but_unauthorized(self):
        unauthorized_user = User.objects.create_user(
            email="unauth@example.com",
            username="unauth@example.com",
            password="password",
            name="No Group User",
            status="active",
        )
        refresh = RefreshToken.for_user(unauthorized_user)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
        response = self.client.get("/api/profiles/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
