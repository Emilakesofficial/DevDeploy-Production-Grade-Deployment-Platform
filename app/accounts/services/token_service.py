import hashlib
import secrets
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from accounts.models import EmailToken, RefreshToken
from django.db import models

class TokenService:
    # Token expiration times
    EMAIL_VERIFICATION_EXPIRY = timedelta(hours=24)
    PASSWORD_RESET_EXPIRY = timedelta(hours=1)
    REFRESH_TOKEN_EXPIRY = timedelta(days=7)
    
    @staticmethod
    def generate_token(length=32):
        """Generates a secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_token(token):
        """Hash a token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @classmethod
    def create_email_token(cls, user, token_type):
        """ Create an email verification or password reset token"""
        raw_token = cls.generate_token()
        token_hash = cls.hash_token(raw_token)
        
        if token_type == 'verify':
            expires_at = timezone.now() + cls.EMAIL_VERIFICATION_EXPIRY
        else:
            expires_at = timezone.now() + cls.PASSWORD_RESET_EXPIRY
            
        email_token = EmailToken.objects.create(
            user=user,
            token_hash=token_hash,
            token_type=token_type,
            expires_at=expires_at
        )
        return raw_token, email_token
    
    @classmethod
    def validate_email_token(cls, raw_token, token_type):
        """Validate an email token, returns EmailToken instance if valid, else None"""
        token_hash = cls.hash_token(raw_token)
        
        try:
            email_token = EmailToken.objects.get(
                token_hash=token_hash,
                token_type=token_type,
                used=False
            )
            
            if not email_token.is_valid():
                return None
            return email_token
        except EmailToken.DoesNotExist:
            return None
     
    @staticmethod
    def mark_token_used(email_token):
        """Mark an email token used"""
        email_token.used = True
        email_token.save(update_fields=['used'])
        
    @classmethod
    def create_refresh_token(cls, user, ip_address='', device_info=None):
        """Create a refresh token, returns tuple(token string, RefreshToken instance)"""
        raw_token = cls.generate_token()
        token_hash = cls.hash_token(raw_token)
        
        refresh_token = RefreshToken.objects.create(
            user=user,
            token_hash=token_hash,
            ip_address=ip_address,
            device_info=device_info,
            expires_at=timezone.now() + cls.REFRESH_TOKEN_EXPIRY
        )
        return raw_token, refresh_token
    
    @classmethod
    def validate_refresh_token(cls, raw_token):
        """Validate a refresh token, returns RefreshToken instance if valid, else None"""
        token_hash = cls.hash_token(raw_token)
        
        try:
            refresh_token = RefreshToken.objects.get(
                token_hash=token_hash,
                revoked=False
            )
            
            if not refresh_token.is_valid():
                return None
            return refresh_token
        except RefreshToken.DoesNotExist:
            return None
        
    @classmethod
    def revoke_refresh_token(cls, refresh_token):
        """Revoke a refresh token"""
        refresh_token.revoked = True
        refresh_token.save(update_fields=['revoked'])
        
    @classmethod
    def revoke_all_user_tokens(cls, user):
        """Revoke all refresh token for a user"""
        RefreshToken.objects.filter(
            user=user,
            revoked=False
        ).update(revoked=True)
        
    @classmethod
    def cleanup_expired_tokens(cls):
        """Delete expired email and refresh tokens"""
        now = timezone.now()
        EmailToken.objects.filter(expires_at__lt=now).delete()
        cutoff_date = now - timedelta(days=30)
        RefreshToken.objects.filter(
            models.Q(expires_at__lt=now) | models.Q(revoked=True),
            created_at__lt=cutoff_date
        ).delete()