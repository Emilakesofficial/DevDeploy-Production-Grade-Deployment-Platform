"""
Integration tests for views
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.services.token_service import TokenService
import json

User = get_user_model()


class RegistrationViewTest(TestCase):
    """Test registration endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
    
    def test_successful_registration(self):
        """Test successful registration"""
        data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertIn('message', response.json())
        
        # Verify user was created
        user = User.objects.get(email='newuser@example.com')
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_verified)
    
    def test_registration_password_mismatch(self):
        """Test registration with password mismatch"""
        data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!'
        }
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)


class LoginViewTest(TestCase):
    """Test login endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            is_active=True,
            is_verified=True
        )
    
    def test_successful_login(self):
        """Test successful login"""
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())
        self.assertIn('user', response.json())
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword123!'
        }
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_login_unverified_user(self):
        """Test login with unverified user"""
        unverified = User.objects.create_user(
            email='unverified@example.com',
            password='TestPass123!',
            is_active=False,
            is_verified=False
        )
        
        data = {
            'email': 'unverified@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('not active', response.json()['error'].lower())