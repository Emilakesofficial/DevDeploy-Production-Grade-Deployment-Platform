import uuid
from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    ACTION_CHOICES = [
        # Authentication
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('logout', 'Logout'),
        ('token_refresh', 'Token Refresh'),
        
        # Registration
        ('register', 'User Registration'),
        ('email_verified', 'Email Verified'),
        
        # Password
        ('password_reset_request', 'Password Reset Request'),
        ('password_reset_success', 'Password Reset Success'),
        ('password_changed', 'Password Changed'),
        
        # Profile
        ('profile_updated', 'Profile Updated'),
        ('account_deleted', 'Account Deleted'),
        
        # Security
        ('account_locked', 'Account Locked'),
        ('suspicious_activity', 'Suspicious Activity Detected'),
        ('token_revoked', 'Token Revoked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True, 
        related_name='audit_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
        
    def __str__(self):
        user_email = self.user.email if self.user else 'Anonymous'
        return f"{self.get_action_display()} by {user_email} at {self.timestamp}"
