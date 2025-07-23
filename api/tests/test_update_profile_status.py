from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import Profile, InviteCode

User = get_user_model()

class UpdateProfileStatusAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_group = Group.objects.create(name="Admin")

        # Create a user and invite code
        self.creator = User.objects.create_user(
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
            created_by=self.creator,
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

        self.profile = Profile.objects.create(
            user=self.user,
            invite_code=self.invite_code,
            street_address="123 Main St",
            city="Lexington",
            state="KY",
            zipcode="40502",
            phone="555-123-4567",
            status="pending",
        )

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

       # Authorized admin user
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin@example.com",
            password="securepassword",
            name="Admin",
            status="active",
        )
        self.admin_user.groups.add(self.admin_group)
        refresh = RefreshToken.for_user(self.admin_user)
        self.admin_token = str(refresh.access_token)

    def test_update_status_requires_authentication(self):
        """Unauthenticated users cannot update profile status."""
        response = self.client.patch(f"/api/profiles/{self.profile.id}/review/", {"status": "approved"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_status_success(self):
        """Authenticated Admin user can update profile status."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.patch(f"/api/profiles/{self.profile.id}/review/", {"status": "approved"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, "approved")
        self.assertEqual(response.data["status"], "approved")

    def test_update_status_invalid_value(self):
        """Invalid status value returns 400."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.patch(f"/api/profiles/{self.profile.id}/review/", {"status": "not_a_valid_status"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_update_status_does_not_change_other_fields(self):
        """Ensure only the status field is modified."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        original_address = self.profile.street_address
        response = self.client.patch(f"/api/profiles/{self.profile.id}/review/", {"status": "rejected"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, "rejected")
        self.assertEqual(self.profile.street_address, original_address)

    def test_update_status_invalid_profile_id(self):
        """Returns 404 for non-existent profile."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.patch("/api/profiles/9999/review/", {"status": "approved"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
