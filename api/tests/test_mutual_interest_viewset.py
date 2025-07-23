from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import Church, Profile, InviteCode, Job, MutualInterest

User = get_user_model()


class MutualInterestMatchesTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Set up church and job
        self.church = Church.objects.create(
            name="Grace Church",
            email="info@grace.org",
            phone="555-123-4567",
            website="https://grace.org",
            street_address="100 Main St",
            city="Lexington",
            state="KY",
            zipcode="40502",
            status="active",
        )

        self.church_user = User.objects.create_user(
            email="admin@grace.org",
            username="admin@grace.org",
            password="securepassword",
            name="Church Admin",
            status="active",
            church_id=self.church,
        )

        self.job = Job.objects.create(
            church=self.church,
            title="Youth Pastor",
            ministry_type="Youth",
            employment_type="Full Time",
            job_description="Lead youth ministry",
            about_church="Grace is a growing church",
            job_url_link="https://jobs.example.org/1",
            status="approved",
        )

        # Set up candidate and profile
        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            username="candidate@example.com",
            password="securepassword",
            name="Candidate User",
            status="active",
        )

        self.profile = Profile.objects.create(
            user=self.candidate,
            street_address="456 Elm St",
            city="Lexington",
            state="KY",
            zipcode="40502",
            phone="555-987-6543",
            status="approved",
        )

        # Auth token for church user
        refresh = RefreshToken.for_user(self.church_user)
        self.church_token = str(refresh.access_token)

    def test_mutual_match_shown_only_when_both_sides_expressed(self):
        """Mutual match only appears when both church and candidate express interest"""
        # Only one side expresses interest → no match yet
        MutualInterest.objects.create(
            job_listing=self.job,
            profile=self.profile,
            expressed_by="candidate",
            expressed_by_user=self.candidate,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.church_token}")
        response = self.client.get("/api/mutual-interests/matches/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # Now church expresses interest too → match becomes mutual
        MutualInterest.objects.create(
            job_listing=self.job,
            profile=self.profile,
            expressed_by="church",
            expressed_by_user=self.church_user,
        )

        response = self.client.get("/api/mutual-interests/matches/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["job_listing"], self.job.id)
        self.assertEqual(response.data[0]["profile"], self.profile.id)
        self.assertTrue(response.data[0]["is_mutual"])

    def test_mutual_matches_filter_by_job_listing(self):
        """Church user can filter mutual matches by job_listing query param"""
        # Create a second job
        other_job = Job.objects.create(
            church=self.church,
            title="Worship Leader",
            ministry_type="Worship",
            employment_type="Part Time",
            job_description="Lead worship",
            about_church="Grace Church",
            job_url_link="https://jobs.example.org/2",
            status="approved",
        )

        # Create another candidate & profile
        candidate2 = User.objects.create_user(
            email="second@example.com",
            username="second@example.com",
            password="securepassword",
            name="Second Candidate",
            status="active",
        )
        profile2 = Profile.objects.create(
            user=candidate2,
            street_address="789 Oak St",
            city="Lexington",
            state="KY",
            zipcode="40503",
            phone="555-333-2222",
            status="approved",
        )

        # First mutual interest: job1/profile1
        MutualInterest.objects.create(
            job_listing=self.job,
            profile=self.profile,
            expressed_by="candidate",
            expressed_by_user=self.candidate,
        )
        MutualInterest.objects.create(
            job_listing=self.job,
            profile=self.profile,
            expressed_by="church",
            expressed_by_user=self.church_user,
        )

        # Second mutual interest: other_job/profile2
        MutualInterest.objects.create(
            job_listing=other_job,
            profile=profile2,
            expressed_by="candidate",
            expressed_by_user=candidate2,
        )
        MutualInterest.objects.create(
            job_listing=other_job,
            profile=profile2,
            expressed_by="church",
            expressed_by_user=self.church_user,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.church_token}")

        # Filter by original job
        response = self.client.get(
            f"/api/mutual-interests/matches/?job_listing={self.job.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["job_listing"], self.job.id)
        self.assertEqual(response.data[0]["profile"], self.profile.id)

        # Filter by second job
        response = self.client.get(
            f"/api/mutual-interests/matches/?job_listing={other_job.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["job_listing"], other_job.id)
        self.assertEqual(response.data[0]["profile"], profile2.id)

    def test_mutual_matches_invalid_job_listing(self):
        """Returns 404 if church user filters by a job not owned by their church"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.church_token}")
        response = self.client.get("/api/mutual-interests/matches/?job_listing=999999")
        self.assertEqual(response.status_code, 404)


class MutualInterestAdminMatchesTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create groups
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")

        # Create a church and job
        self.church = Church.objects.create(
            name="Faith Church",
            email="info@faithchurch.com",
            phone="+12345678901",
            website="http://faithchurch.com",
            street_address="123 Church St",
            city="Lexington",
            state="KY",
            zipcode="40502",
            status="active",
        )

        self.job = Job.objects.create(
            church=self.church,
            title="Youth Pastor",
            ministry_type="Youth",
            employment_type="Full Time",
            job_description="Lead youth ministry",
            about_church="A great place to grow",
            job_url_link="http://faithchurch.com/jobs/1",
            status="approved",
        )

        # Create users
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin@example.com",
            password="adminpass",
            name="Admin User",
            status="active",
        )
        self.admin_user.groups.add(self.admin_group)

        self.non_admin_user = User.objects.create_user(
            email="user@example.com",
            username="user@example.com",
            password="userpass",
            name="Regular User",
            status="active",
        )

        # Create invite code and candidate profile
        self.invite_code = InviteCode.objects.create(
            code="JOIN2024",
            event="Spring Hiring",
            used_count=0,
            status="active",
            created_by=self.admin_user,
            expires_at="2099-01-01T00:00:00Z",
        )

        self.profile = Profile.objects.create(
            user=self.non_admin_user,
            invite_code=self.invite_code,
            street_address="123 Main St",
            city="Lexington",
            state="KY",
            zipcode="40502",
            phone="555-555-5555",
            status="approved",
        )

        # Create mutual interest from both sides
        MutualInterest.objects.create(
            job_listing=self.job,
            profile=self.profile,
            expressed_by="candidate",
            expressed_by_user=self.non_admin_user,
        )
        MutualInterest.objects.create(
            job_listing=self.job,
            profile=self.profile,
            expressed_by="church",
            expressed_by_user=self.admin_user,
        )

        # Get tokens
        self.admin_token = str(RefreshToken.for_user(self.admin_user).access_token)
        self.user_token = str(RefreshToken.for_user(self.non_admin_user).access_token)

    def test_admin_can_access_admin_matches(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.admin_token)
        response = self.client.get("/api/mutual-interests/admin-matches/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_non_admin_cannot_access_admin_matches(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.user_token)
        response = self.client.get("/api/mutual-interests/admin-matches/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
