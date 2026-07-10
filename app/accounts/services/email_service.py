"""
Service for email operations
"""
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.utils import timezone



class EmailService:
    """Service class for email operations"""
    
    FROM_EMAIL = settings.DEFAULT_FROM_EMAIL
    FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'https://example.com') # ttps://localhost:3000
    
    @classmethod
    def send_email(cls, to_email, subject, html_content, text_content=None):
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content (optional)
        """
        if text_content is None:
            text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=cls.FROM_EMAIL,
            to=[to_email]
        )
        email.attach_alternative(html_content, "text/html")
        result = email.send(fail_silently=False)
        
        if result == 0:
            raise Exception("Email was not sent (SMTP returned 0)")
    
    @classmethod
    def send_welcome_email(cls, user):
        """Send welcome email to new user"""
        subject = 'Welcome to Financial Auth Service'
        html_content = render_to_string('emails/welcome.html', {
            'user': user,
        })
        cls.send_email(user.email, subject, html_content)
    
    @classmethod
    def send_verification_email(cls, user, verification_token):
        """Send email verification link"""
        # In production, this would be your frontend URL
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        
        subject = 'Verify Your Email Address'
        html_content = render_to_string('emails/verification.html', {
            'user': user,
            'verification_url': verification_url
        })
        cls.send_email(user.email, subject, html_content)
    
    @classmethod
    def send_password_reset_email(cls, user, reset_token):
        """Send password reset link"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = 'Password Reset Request'
        html_content = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_url': reset_url,
        })
        cls.send_email(user.email, subject, html_content)
    
    @classmethod
    def send_suspicious_activity_alert(cls, user, activity_details):
        """Send alert for suspicious login activity"""
        subject = '⚠️ Security Alert - Unusual Login Activity'
        html_content = render_to_string('emails/suspicious_activity.html', {
            'user': user,
            'ip_address': activity_details.get('ip_address'),
            'timestamp': activity_details.get('timestamp'),
            'device_info': activity_details.get('device_info'),
            'reason': activity_details.get('reason'),
        })
        cls.send_email(user.email, subject, html_content)
    
    @classmethod
    def send_password_changed_email(cls, user):
        """Send notification that password was changed"""
        subject = 'Password Changed Successfully'
        html_content = render_to_string('emails/password_changed.html', {
            'user': user,
            'timestamp': timezone.now(),
        })
        cls.send_email(user.email, subject, html_content)