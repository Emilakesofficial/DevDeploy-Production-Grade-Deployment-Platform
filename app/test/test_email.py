#!/usr/bin/env python
"""
Test script for email functionality
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User
from accounts.tasks import (
    send_welcome_email_task,
    send_verification_email_task,
    send_password_reset_email_task,
)


def test_emails():
    """Test sending emails"""
    # Get or create a test user
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'User',
            'is_active': True,
            'is_verified': True,
        }
    )
    
    if created:
        user.set_password('TestPassword123!')
        user.save()
    
    print(f"Testing with user: {user.email}")
    
    # Test welcome email
    print("\n1. Testing welcome email...")
    result = send_welcome_email_task.delay(str(user.id))
    print(f"Task ID: {result.id}")
    print(f"Task status: {result.status}")
    
    # Test verification email
    print("\n2. Testing verification email...")
    test_token = "test-verification-token-12345"
    result = send_verification_email_task.delay(str(user.id), test_token)
    print(f"Task ID: {result.id}")
    print(f"Task status: {result.status}")
    
    # Test password reset email
    print("\n3. Testing password reset email...")
    test_reset_token = "test-reset-token-67890"
    result = send_password_reset_email_task.delay(str(user.id), test_reset_token)
    print(f"Task ID: {result.id}")
    print(f"Task status: {result.status}")
    
    print("\n✅ All email tasks queued successfully!")
    print("Check your email inbox and Celery worker logs.")


if __name__ == '__main__':
    test_emails()