"""
Unit tests for services
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.services.security_service import SecurityService
from accounts.services.token_service import TokenService
from accounts.services.auth_service import AuthService

User = get_user_model()


class SecurityServiceTest(TestCase):
    """Test SecurityService"""
    
    def test_password_validation_valid(self):
        """Test valid password"""
        is_valid, error = SecurityService.validate_password_strength('ValidPass123!')
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_password_validation_too_short(self):
        """Test password too short"""
        is_valid, error = SecurityService.validate_password_strength('Short1!')
        self.assertFalse(is_valid)
        self.assertIn('8 characters', error)
    
    def test_password_validation_no_uppercase(self):
        """Test password without uppercase"""
        is_valid, error = SecurityService.validate_password_strength('lowercase123!')
        self.assertFalse(is_valid)
        self.assertIn('uppercase', error)
    
    def test_password_validation_no_digit(self):
        """Test password without digit"""
        is_valid, error = SecurityService.validate_password_strength('NoDigits!')
        self.assertFalse(is_valid)
        self.assertIn('digit', error)


class TokenServiceTest(TestCase):
    """Test TokenService"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_generate_token(self):
        """Test token generation"""
        token = TokenService.generate_token()
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 20)
    
    def test_hash_token(self):
        """Test token hashing"""
        token = 'test-token'
        hash1 = TokenService.hash_token(token)
        hash2 = TokenService.hash_token(token)
        
        # Same token should produce same hash
        self.assertEqual(hash1, hash2)
        
        # Different token should produce different hash
        hash3 = TokenService.hash_token('different-token')
        self.assertNotEqual(hash1, hash3)


class AuthServiceTest(TestCase):
    """Test AuthService"""
    
    def test_register_user_success(self):
        """Test successful user registration"""
        user, error = AuthService.register_user(
            email='newuser@example.com',
            password='SecurePass123!',
            first_name='New',
            last_name='User'
        )
        
        self.assertIsNone(error)
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_verified)
    
    def test_register_user_weak_password(self):
        """Test registration with weak password"""
        user, error = AuthService.register_user(
            email='weak@example.com',
            password='weak',
            first_name='Weak',
            last_name='Password'
        )
        
        self.assertIsNone(user)
        self.assertIsNotNone(error)
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        User.objects.create_user(
            email='existing@example.com',
            password='Pass123!'
        )
        
        user, error = AuthService.register_user(
            email='existing@example.com',
            password='NewPass123!',
            first_name='Test',
            last_name='User'
        )
        
        self.assertIsNone(user)
        self.assertIn('already exists', error)