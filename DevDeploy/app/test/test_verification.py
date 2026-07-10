#!/usr/bin/env python
"""
Test email verification
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import requests
from accounts.models import User, EmailToken
from accounts.services.token_service import TokenService

BASE_URL = "http://localhost:8000/api/auth"


def test_verification():
    """Test email verification"""
    print("\n" + "="*60)
    print("Testing Email Verification")
    print("="*60)
    
    # Get user
    try:
        user = User.objects.get(email='testuser@example.com')
        print(f"\nUser found: {user.email}")
        print(f"Is Active: {user.is_active}")
        print(f"Is Verified: {user.is_verified}")
    except User.DoesNotExist:
        print("User not found. Please run test_registration.py first.")
        return
    
    # Create a test token
    test_token = TokenService.generate_token()
    token_hash = TokenService.hash_token(test_token)
    
    # Get or create email token
    email_token = EmailToken.objects.filter(
        user=user,
        token_type='verify',
        used=False
    ).first()
    
    if email_token:
        email_token.token_hash = token_hash
        email_token.save()
        print(f"\nToken updated: {test_token}")
    else:
        print("No verification token found")
        return
    
    # Test verification
    print("\nTesting verification endpoint...")
    response = requests.post(
        f"{BASE_URL}/verify-email/",
        json={"token": test_token}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Check user status
    user.refresh_from_db()
    print(f"\nAfter verification:")
    print(f"Is Active: {user.is_active}")
    print(f"Is Verified: {user.is_verified}")
    
    # Test with same token (should fail - token already used)
    print("\nTesting with already used token...")
    response = requests.post(
        f"{BASE_URL}/verify-email/",
        json={"token": test_token}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    print("\n" + "="*60)
    print("✅ Verification tests completed!")
    print("="*60)


if __name__ == '__main__':
    test_verification()