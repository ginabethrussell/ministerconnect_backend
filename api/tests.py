# These tests use Django's test framework, which creates a temporary database for testing.
# All data created, updated, or deleted in these tests is isolated and does not affect your real database.
# After the tests finish, the test database is deleted automatically.

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Church

class ChurchAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_payload = {
            "name": "Test Church",
            "email": "test@church.com",
            "phone": "+14155552671",
            "website": "https://testchurch.com",
            "street_address": "123 Main St",
            "city": "Springfield",
            "state": "CA",
            "zipcode": "90210",
            "status": "active"
        }

    def test_create_church_success(self):
        response = self.client.post('/api/churches/create/', self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Church.objects.count(), 1)
        self.assertEqual(Church.objects.get().name, "Test Church")

    def test_create_duplicate_church(self):
        # Create the first church
        self.client.post('/api/churches/create/', self.valid_payload, format='json')
        # Try to create a duplicate
        response = self.client.post('/api/churches/create/', self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('A church with this name, city, and state already exists.', str(response.data))

    def test_invalid_state(self):
        payload = self.valid_payload.copy()
        payload['state'] = 'California'
        response = self.client.post('/api/churches/create/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('is not a valid choice', str(response.data))

    def test_invalid_phone(self):
        payload = self.valid_payload.copy()
        payload['phone'] = '123'
        response = self.client.post('/api/churches/create/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Enter a valid phone number.', str(response.data))

    def test_invalid_zipcode(self):
        payload = self.valid_payload.copy()
        payload['zipcode'] = 'abcde'
        response = self.client.post('/api/churches/create/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Enter a valid US ZIP code.', str(response.data))
