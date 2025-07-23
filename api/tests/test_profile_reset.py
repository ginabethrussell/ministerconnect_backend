from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import Profile, InviteCode

User = get_user_model()


class ProfileResetAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create a user to use as the creator of the invite code
        self.creator = User.objects.create_user(
            email="creator@example.com",
            username="creator@example.com",
            password="password",
            name="Creator User",
            status="active",
        )

        # Create an invite code
        self.invite_code = InviteCode.objects.create(
            code="CANDIDATE2024",
            event="Spring 2024 Registration",
            used_count=0,
            status="active",
            created_by=self.creator,
            expires_at="2099-12-31T23:59:59Z",
        )

        # Create a test user
        self.user = User.objects.create_user(
            email="candidate@example.com",
            username="candidate@example.com",
            password="securepassword",
            name="Test Candidate",
            status="active",
            invite_code=self.invite_code,
        )

        # Create a profile with some data
        self.profile = Profile.objects.create(
            user=self.user,
            invite_code=self.invite_code,
            street_address="123 Main St",
            city="Lexington",
            state="KY",
            zipcode="40502",
            phone="555-123-4567",
            status="pending",
            video_url="https://example.com/video",
            placement_preferences=["Youth Ministry", "Worship"],
            submitted_at="2024-01-01T12:00:00Z",
        )

        # Create JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_reset_profile_requires_authentication(self):
        """Test that profile reset requires authentication."""
        response = self.client.post("/api/profile/reset/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reset_profile_success(self):
        """Test successful profile reset."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # Verify profile has data before reset
        self.assertEqual(self.profile.street_address, "123 Main St")
        self.assertEqual(self.profile.status, "pending")
        self.assertEqual(self.profile.phone, "555-123-4567")

        # Reset the profile
        response = self.client.post("/api/profile/reset/")

        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("detail", response.data)
        self.assertIn("profile", response.data)
        self.assertEqual(
            response.data["detail"], "Profile reset to draft successfully."
        )

        # Verify profile was reset
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.status, "draft")
        self.assertEqual(profile.street_address, "")
        self.assertEqual(profile.city, "")
        self.assertEqual(profile.state, "")
        self.assertEqual(profile.zipcode, "")
        self.assertIsNone(profile.phone)
        self.assertIsNone(profile.video_url)
        self.assertEqual(profile.placement_preferences, [])
        self.assertIsNone(profile.submitted_at)

        # Verify user and invite_code relationships are preserved
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.invite_code, self.invite_code)

    def test_reset_profile_response_format(self):
        """Test that the response contains the expected format."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post("/api/profile/reset/")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check response structure
        self.assertIn("detail", response.data)
        self.assertIn("profile", response.data)

        # Check profile data structure
        profile_data = response.data["profile"]
        expected_fields = [
            "id",
            "user",
            "invite_code",
            "invite_code_string",
            "street_address",
            "city",
            "state",
            "zipcode",
            "phone",
            "status",
            "resume",
            "video_url",
            "placement_preferences",
            "submitted_at",
            "created_at",
            "updated_at",
        ]

        for field in expected_fields:
            self.assertIn(field, profile_data)

        # Check specific values
        self.assertEqual(profile_data["status"], "draft")
        self.assertEqual(profile_data["street_address"], "")
        self.assertEqual(profile_data["city"], "")
        self.assertEqual(profile_data["state"], "")
        self.assertEqual(profile_data["zipcode"], "")
        self.assertIsNone(profile_data["phone"])
        self.assertIsNone(profile_data["video_url"])
        self.assertEqual(profile_data["placement_preferences"], [])
        self.assertIsNone(profile_data["submitted_at"])

    def test_reset_profile_creates_new_profile_instance(self):
        """Test that reset creates a new profile instance (different ID)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        original_profile_id = self.profile.id

        response = self.client.post("/api/profile/reset/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify a new profile was created
        new_profile_id = response.data["profile"]["id"]
        self.assertNotEqual(original_profile_id, new_profile_id)

        # Verify the old profile no longer exists
        with self.assertRaises(Profile.DoesNotExist):
            Profile.objects.get(id=original_profile_id)

    def test_reset_profile_preserves_user_and_invite_code(self):
        """Test that user and invite_code relationships are preserved after reset."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        response = self.client.post("/api/profile/reset/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        profile_data = response.data["profile"]

        # Check that relationships are preserved
        self.assertEqual(profile_data["user"], self.user.id)
        self.assertEqual(profile_data["invite_code"], self.invite_code.id)
        self.assertEqual(profile_data["invite_code_string"], self.invite_code.code)

    def test_reset_profile_multiple_times(self):
        """Test that profile can be reset multiple times."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # First reset
        response1 = self.client.post("/api/profile/reset/")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Add some data to the profile
        profile = Profile.objects.get(user=self.user)
        profile.street_address = "456 New St"
        profile.city = "New City"
        profile.status = "approved"
        profile.save()

        # Second reset
        response2 = self.client.post("/api/profile/reset/")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        # Verify profile was reset again
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.status, "draft")
        self.assertEqual(profile.street_address, "")
        self.assertEqual(profile.city, "")
