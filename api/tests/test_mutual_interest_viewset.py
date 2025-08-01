from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import Group
from api.models import User, Church, Job, Profile, MutualInterest


class MutualInterestMatchViewSetTests(APITestCase):
    def setUp(self):
        self.church = Church.objects.create(name="Test Church")
        self.church_user = User.objects.create_user(
            email="church@example.com",
            username="church@example.com",
            password="securepassword",
            name="Church User",
            status="active",
            church_id=self.church,
        )
        church_group = Group.objects.get_or_create(name="Church User")[0]
        self.church_user.groups.set([church_group])
        self.client.login(username="church@example.com", password="securepassword")

        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            username="candidate@example.com",
            password="securepassword",
            name="Candidate User",
            status="active",
        )
        self.profile = Profile.objects.create(
            user=self.candidate,
            street_address="123 Test St",
            city="Lexington",
            state="KY",
            zipcode="40503",
            phone="555-555-5555",
            status="approved",
        )

        self.job = Job.objects.create(
            church=self.church,
            title="Youth Pastor",
            ministry_type="Youth",
            employment_type="Full Time",
            job_description="Lead youth ministry",
            about_church="A welcoming church community.",
            job_url_link="https://jobs.example.org/youth",
            status="approved",
        )

    def test_no_match_with_single_interest(self):
        MutualInterest.objects.create(
            job_listing=self.job,
            profile=self.profile,
            expressed_by="candidate",
            expressed_by_user=self.candidate,
        )

        url = reverse("mutual-interest-mutual-matches")
        self.client.force_authenticate(user=self.church_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_mutual_match_found(self):
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

        url = reverse("mutual-interest-mutual-matches")
        self.client.force_authenticate(user=self.church_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_invalid_job_filter_returns_404(self):
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

        url = reverse("mutual-interest-mutual-matches") + "?job_listing=999999"
        self.client.force_authenticate(user=self.church_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
