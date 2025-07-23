from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import Profile, InviteCode

User = get_user_model()


class ProfileMeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a user and invite code
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
        self.profile = Profile.objects.create(
            user=self.user,
            invite_code=self.invite_code,
            street_address="123 Main St",
            city="Lexington",
            state="KY",
            zipcode="40502",
            status="draft",
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_get_profile_me_success(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        response = self.client.get("/api/profile/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.profile.id)
        self.assertEqual(response.data["user"], self.user.id)
        self.assertEqual(response.data["invite_code"], self.invite_code.id)
        self.assertEqual(response.data["status"], "draft")

    def test_get_profile_me_unauthenticated(self):
        self.client.credentials()  # Remove auth
        response = self.client.get("/api/profile/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_profile_me_status(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        pdf_content = b"%PDF-1.4 test pdf content"
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf", pdf_content, content_type="application/pdf"
        )
        data = {
            "status": "pending",
            "phone": "+15551234567",
            "street_address": "123 Main St",
            "city": "Lexington",
            "state": "KY",
            "zipcode": "40502",
            "resume": pdf_file,
        }
        response = self.client.patch("/api/profile/me/", data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "pending")

    def test_put_profile_me_full_update(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        # Simulate a PDF upload
        pdf_content = b"%PDF-1.4 test pdf content"
        pdf_file = SimpleUploadedFile(
            "test_resume.pdf", pdf_content, content_type="application/pdf"
        )
        data = {
            "street_address": "456 New St",
            "city": "New City",
            "state": "NY",
            "zipcode": "10001",
            "placement_preferences": '["Music Ministry"]',
            "status": "approved",
            "resume": pdf_file,
        }
        response = self.client.put("/api/profile/me/", data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["city"], "New City")
        self.assertEqual(response.data["status"], "approved")
        self.assertIn("test_resume", response.data["resume"])
