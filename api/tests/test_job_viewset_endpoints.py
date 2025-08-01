from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import Church, Job

User = get_user_model()


class JobViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create a church
        self.church = Church.objects.create(
            name="Grace Fellowship Church",
            email="info@gracefellowship.org",
            phone="555-123-4567",
            website="https://gracefellowship.org",
            street_address="123 Main St",
            city="Lexington",
            state="KY",
            zipcode="40502",
            status="active",
        )

        # Create a user and link to church
        self.user = User.objects.create_user(
            email="staff@gracefellowship.org",
            username="staff@gracefellowship.org",
            password="securepassword",
            name="Church Staff",
            status="active",
            church_id=self.church,
        )

        # Add the user to the Church User group
        church_group = Group.objects.get_or_create(name="Church User")[0]
        self.user.groups.set([church_group])

        # Auth token
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # Create a job
        self.job = Job.objects.create(
            church=self.church,
            title="Youth Pastor",
            ministry_type="Youth",
            employment_type="Full Time with Benefits",
            job_description="Lead our youth ministry...",
            about_church="Grace Fellowship is a vibrant church...",
            job_url_link="https://jobs.efca.org/jobs/1129",
            status="pending",
        )

    def test_list_jobs(self):
        """GET /api/jobs/ should return job list"""
        response = self.client.get("/api/jobs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["id"], self.job.id)

    def test_retrieve_job(self):
        """GET /api/jobs/<id>/ should return job details"""
        response = self.client.get(f"/api/jobs/{self.job.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Youth Pastor")

    def test_create_job(self):
        """POST /api/jobs/ should create a new job"""
        job_data = {
            "church": self.church.id,
            "title": "Associate Pastor",
            "ministry_type": "Adult",
            "employment_type": "Part Time",
            "job_description": "Assist lead pastor with adult ministries...",
            "about_church": "We are a church in growth mode...",
            "job_url_link": "https://example.com/job",
            "status": "pending",
        }
        response = self.client.post("/api/jobs/", job_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Associate Pastor")

    def test_update_job(self):
        """PATCH /api/jobs/<id>/ should update fields"""
        response = self.client.patch(
            f"/api/jobs/{self.job.id}/", {"status": "approved"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, "approved")

    def test_delete_job(self):
        """DELETE /api/jobs/<id>/ should delete the job"""
        response = self.client.delete(f"/api/jobs/{self.job.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Job.objects.filter(id=self.job.id).exists())

    def test_filter_jobs_by_status(self):
        """GET /api/jobs/?status=pending filters results"""
        Job.objects.create(
            church=self.church,
            title="Worship Leader",
            ministry_type="Worship",
            employment_type="Full Time",
            job_description="Lead music and worship...",
            about_church="We value vibrant worship...",
            job_url_link="https://example.com/worship",
            status="approved",
        )

        response = self.client.get("/api/jobs/?status=pending")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Youth Pastor")

    def test_filter_jobs_by_church(self):
        """GET /api/jobs/?church=<id> filters jobs by church"""
        other_church = Church.objects.create(
            name="Other Church",
            email="info@other.org",
            phone="555-000-0000",
            website="https://otherchurch.org",
            street_address="999 Side St",
            city="Louisville",
            state="KY",
            zipcode="40202",
            status="active",
        )

        Job.objects.create(
            church=other_church,
            title="Teaching Pastor",
            ministry_type="Preaching",
            employment_type="Full Time",
            job_description="Lead teaching ministry...",
            about_church="Bible-centered teaching church...",
            job_url_link="https://example.com/teach",
            status="pending",
        )

        response = self.client.get(f"/api/jobs/?church={self.church.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for job in response.data["results"]:
            self.assertEqual(job["church"]["id"], self.church.id)
