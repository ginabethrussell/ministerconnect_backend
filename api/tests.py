# These tests use Django's test framework, which creates a temporary database for testing.
# All data created, updated, or deleted in these tests is isolated and does not affect your real database.
# After the tests finish, the test database is deleted automatically.

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import Church, InviteCode
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

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
         # Create a user and get a token
        self.user = User.objects.create_user(
            email="authuser@church.org",
            username="authuser@church.org",
            password="securepassword",
            name="Auth User",
            status="active"
        )
        # Get JWT token for the user
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_create_church_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.post('/api/churches/create/', self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Church.objects.count(), 1)
        self.assertEqual(Church.objects.get().name, "Test Church")

    def test_create_duplicate_church(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        # Create the first church
        self.client.post('/api/churches/create/', self.valid_payload, format='json')
        # Try to create a duplicate
        response = self.client.post('/api/churches/create/', self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('A church with this name, city, and state already exists.', str(response.data))

    def test_invalid_state(self):
        payload = self.valid_payload.copy()
        payload['state'] = 'California'
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.post('/api/churches/create/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('is not a valid choice', str(response.data))

    def test_invalid_phone(self):
        payload = self.valid_payload.copy()
        payload['phone'] = '123'
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.post('/api/churches/create/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Enter a valid phone number.', str(response.data))

    def test_invalid_zipcode(self):
        payload = self.valid_payload.copy()
        payload['zipcode'] = 'abcde'
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.post('/api/churches/create/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Enter a valid US ZIP code.', str(response.data))

class UserAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.church = Church.objects.create(
            name="Test Church",
            email="test@church.com",
            phone="+14155552671",
            website="https://testchurch.com",
            street_address="123 Main St",
            city="Springfield",
            state="CA",
            zipcode="90210",
            status="active"
        )
         # Create a user and get a token
        self.user = User.objects.create_user(
            email="authuser@church.org",
            username="authuser@church.org",
            password="securepassword",
            name="Auth User",
            status="active"
        )
          # Get JWT token for the user
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        Group.objects.get_or_create(name="Church User")
        self.valid_payload = {
            "email": "user@church.org",
            "username": "user@church.org",
            "name": "Jane Doe",
            "password": "securepassword",
            "groups": ["Church User"],
            "church_id": self.church.id,
            "status": "pending",
            "requires_password_change": True
        }

    def test_create_user_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.post('/api/users/create/', self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertTrue(User.objects.filter(email="user@church.org").exists())

    def test_create_user_bad_request(self):
        payload = self.valid_payload.copy()
        del payload['email']  # Remove required field
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.post('/api/users/create/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_create_user_church_not_found(self):
        payload = self.valid_payload.copy()
        payload['church_id'] = 9999  # Non-existent church ID
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.post('/api/users/create/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('church_id', response.data)

    def test_create_user_duplicate(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        # Create the user once
        self.client.post('/api/users/create/', self.valid_payload, format='json')
        # Try to create the same user again
        response = self.client.post('/api/users/create/', self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

class AuthenticatedEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a user and get a token
        self.user = User.objects.create_user(
            email="authuser@church.org",
            username="authuser@church.org",
            password="securepassword",
            name="Auth User",
            status="active"
        )
        self.church = Church.objects.create(
            name="Auth Church",
            email="auth@church.com",
            phone="+14155552671",
            website="https://authchurch.com",
            street_address="123 Main St",
            city="Springfield",
            state="CA",
            zipcode="90210",
            status="active"
        )
        # Get JWT token for the user
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.church_payload = {
            "name": "Protected Church",
            "email": "protected@church.com",
            "phone": "+14155552671",
            "website": "https://protectedchurch.com",
            "street_address": "456 Main St",
            "city": "Springfield",
            "state": "CA",
            "zipcode": "90210",
            "status": "active"
        }

    def test_protected_endpoint_requires_auth(self):
        # Try without authentication
        response = self.client.post('/api/churches/create/', self.church_payload, format='json')
        self.assertEqual(response.status_code, 401)  # Unauthorized

    def test_protected_endpoint_with_auth(self):
        # Set the Authorization header
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.post('/api/churches/create/', self.church_payload, format='json')
        self.assertIn(response.status_code, [200, 201])  # Created or OK

class JWTAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="jwtuser@church.org",
            email="jwtuser@church.org",
            password="securepassword",
            name="JWT User",
            status="active",
            is_active=True
        )

    def test_token_obtain(self):
        response = self.client.post('/api/token/', {
            "email": "jwtuser@church.org",
            "password": "securepassword"
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.access_token = response.data['access']
        self.refresh_token = response.data['refresh']

    def test_token_refresh(self):
        # First, obtain a refresh token
        response = self.client.post('/api/token/', {
            "email": "jwtuser@church.org",
            "password": "securepassword"
        }, format='json')
        refresh_token = response.data['refresh']
        # Now, refresh the access token
        response = self.client.post('/api/token/refresh/', {
            "refresh": refresh_token
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

class InviteCodeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="inviteuser@church.org",
            email="inviteuser@church.org",
            password="securepassword",
            name="Invite User",
            status="active",
            is_active=True
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_create_invite_code_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        payload = {
            "code": "CHURCH2024",
            "event": "Spring 2024 Church Registration",
            "expires_at": "2024-12-31T23:59:59Z"
        }
        response = self.client.post('/api/invite-codes/create/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['code'], "CHURCH2024")
        self.assertEqual(response.data['event'], "Spring 2024 Church Registration")
        self.assertEqual(response.data['status'], "active")
        self.assertEqual(response.data['created_by'], self.user.id)
        self.assertEqual(response.data['created_by_name'], self.user.name)

    def test_create_invite_code_unauthenticated(self):
        payload = {
            "code": "CHURCH2025",
            "event": "Spring 2025 Church Registration",
            "expires_at": "2025-12-31T23:59:59Z"
        }
        response = self.client.post('/api/invite-codes/create/', payload, format='json')
        self.assertEqual(response.status_code, 401)

    def test_create_invite_code_missing_fields(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        payload = {
            "event": "Spring 2024 Church Registration"
            # Missing 'code' and 'expires_at'
        }
        response = self.client.post('/api/invite-codes/create/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('code', response.data)
        self.assertIn('expires_at', response.data)

class InviteCodeListAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="listuser@church.org",
            email="listuser@church.org",
            password="securepassword",
            name="List User",
            status="active",
            is_active=True
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_get_invite_codes_success(self):
        # Create some invite codes
        InviteCode.objects.create(
            code="CODE1",
            event="Event 1",
            expires_at="2024-12-31T23:59:59Z",
            created_by=self.user
        )
        InviteCode.objects.create(
            code="CODE2",
            event="Event 2",
            expires_at="2025-12-31T23:59:59Z",
            created_by=self.user
        )
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.get('/api/invite-codes/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        codes = [item['code'] for item in response.data]
        self.assertIn("CODE1", codes)
        self.assertIn("CODE2", codes)
        for item in response.data:
            self.assertEqual(item['created_by_name'], self.user.name)

    def test_get_invite_codes_unauthenticated(self):
        response = self.client.get('/api/invite-codes/')
        self.assertEqual(response.status_code, 401)

    def test_get_invite_codes_empty(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.get('/api/invite-codes/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
