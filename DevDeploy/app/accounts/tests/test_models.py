"""
Unit tests for models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import RefreshToken, EmailToken
from accounts.services.token_service import TokenService

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_creation(self):
        """Test user is created correctly"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('TestPass123!'))
        self.assertEqual(self.user.get_full_name(), 'Test User')
    
    def test_user_str(self):
        """Test user string representation"""
        self.assertEqual(str(self.user), 'test@example.com')
    
    def test_create_superuser(self):
        """Test superuser creation"""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPass123!'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_verified)


class RefreshTokenModelTest(TestCase):
    """Test RefreshToken model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_token_creation(self):
        """Test refresh token creation"""
        token, token_obj = TokenService.create_refresh_token(
            user=self.user,
            ip_address='127.0.0.1',
            device_info='Test Device'
        )
        
        self.assertEqual(token_obj.user, self.user)
        self.assertEqual(token_obj.ip_address, '127.0.0.1')
        self.assertFalse(token_obj.revoked)
        self.assertTrue(token_obj.is_valid())
    
    def test_token_revocation(self):
        """Test token revocation"""
        token, token_obj = TokenService.create_refresh_token(
            user=self.user,
            ip_address='127.0.0.1'
        )
        
        TokenService.revoke_refresh_token(token_obj)
        self.assertTrue(token_obj.revoked)
        self.assertFalse(token_obj.is_valid())


class EmailTokenModelTest(TestCase):
    """Test EmailToken model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_verification_token_creation(self):
        """Test verification token creation"""
        token, token_obj = TokenService.create_email_token(
            user=self.user,
            token_type='verify'
        )
        
        self.assertEqual(token_obj.user, self.user)
        self.assertEqual(token_obj.token_type, 'verify')
        self.assertFalse(token_obj.used)
        self.assertTrue(token_obj.is_valid())
    
    def test_reset_token_creation(self):
        """Test reset token creation"""
        token, token_obj = TokenService.create_email_token(
            user=self.user,
            token_type='reset'
        )
        
        self.assertEqual(token_obj.token_type, 'reset')
        self.assertTrue(token_obj.is_valid())
    
    def test_token_validation(self):
        """Test token validation"""
        raw_token, token_obj = TokenService.create_email_token(
            user=self.user,
            token_type='verify'
        )
        
        validated = TokenService.validate_email_token(raw_token, 'verify')
        self.assertEqual(validated.id, token_obj.id)
        
        # Invalid token
        invalid = TokenService.validate_email_token('invalid-token', 'verify')
        self.assertIsNone(invalid)