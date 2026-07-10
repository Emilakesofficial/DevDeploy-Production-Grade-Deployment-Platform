#!/usr/bin/env python
"""
Test authentication flow (login, logout, refresh)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import requests
import json
from accounts.models import User

BASE_URL = "http://localhost:8000/api/auth"


class AuthTester:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.user_email = "authtest@example.com"
        self.password = "SecurePass123!"
    
    def print_section(self, title):
        """Print a section header"""
        print("\n" + "="*60)
        print(f" {title}")
        print("="*60)
    
    def create_test_user(self):
        """Create a verified test user"""
        self.print_section("Creating Test User")
        
        # Delete existing user if exists
        User.objects.filter(email=self.user_email).delete()
        
        # Create verified user
        user = User.objects.create_user(
            email=self.user_email,
            password=self.password,
            first_name="Auth",
            last_name="Test",
            is_active=True,
            is_verified=True
        )
        print(f"✓ Created user: {user.email}")
        print(f"  Is Active: {user.is_active}")
        print(f"  Is Verified: {user.is_verified}")
    
    def test_login_success(self):
        """Test successful login"""
        self.print_section("Test 1: Successful Login")
        
        response = requests.post(
            f"{BASE_URL}/login/",
            json={
                "email": self.user_email,
                "password": self.password
            }
        )
        
        print(f"Status: {response.status_code}")
        data = response.json()
        try:
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print("Response is not JSON") 
        
        if response.status_code == 200:
            self.access_token = data.get('access')
            self.refresh_token = data.get('refresh')
            print(f"\n✓ Login successful!")
            print(f"  Access Token: {self.access_token[:50]}...")
            print(f"  Refresh Token: {self.refresh_token[:50]}...")
        else:
            print("✗ Login failed!")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        self.print_section("Test 2: Invalid Credentials")
        
        response = requests.post(
            f"{BASE_URL}/login/",
            json={
                "email": self.user_email,
                "password": "WrongPassword123!"
            }
        )
        
        print(f"Status: {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print("Response is not JSON") 
        
        if response.status_code == 400:
            print("✓ Invalid credentials correctly rejected")
    
    def test_login_unverified_user(self):
        """Test login with unverified user"""
        self.print_section("Test 3: Unverified User")
        
        # Create unverified user
        unverified_email = "unverified@example.com"
        User.objects.filter(email=unverified_email).delete()
        User.objects.create_user(
            email=unverified_email,
            password=self.password,
            first_name="Unverified",
            last_name="User",
            is_active=False,
            is_verified=False
        )
        
        response = requests.post(
            f"{BASE_URL}/login/",
            json={
                "email": unverified_email,
                "password": self.password
            }
        )
        
        print(f"Status: {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print("Response is not JSON") 
        
        if response.status_code == 400:
            print("✓ Unverified user correctly rejected")
    
    def test_rate_limiting(self):
        """Test rate limiting on failed logins"""
        self.print_section("Test 4: Rate Limiting (Failed Attempts)")
        
        temp_email = "ratelimit@example.com"
        User.objects.filter(email=temp_email).delete()
        User.objects.create_user(
            email=temp_email,
            password=self.password,
            first_name="Rate",
            last_name="Limit",
            is_active=True,
            is_verified=True
        )
        
        print("Attempting 6 failed logins...")
        for i in range(6):
            print(f"\nAttempt {i+1}:")
            response = requests.post(
                f"{BASE_URL}/login/",
                json={
                    "email": temp_email,
                    "password": "WrongPassword!"
                }
            )
            
            print(f"  Status: {response.status_code}")
            try:
                print(json.dumps(response.json(), indent=2))
            except Exception:
                print("Response is not JSON") 
            
            if 'locked' in response.json().get('error', '').lower():
                print("\n✓ Account locked after max attempts!")
                break
    
    def test_get_profile(self):
        """Test getting user profile with access token"""
        self.print_section("Test 5: Get User Profile")
        
        if not self.access_token:
            print("✗ No access token available. Login first.")
            return
        
        response = requests.get(
            f"{BASE_URL}/me/",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        print(f"Status: {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print("Response is not JSON") 
        
        if response.status_code == 200:
            print("✓ Successfully retrieved user profile")
    
    def test_get_active_sessions(self):
        """Test getting active sessions"""
        self.print_section("Test 6: Get Active Sessions")
        
        if not self.access_token:
            print("✗ No access token available. Login first.")
            return
        
        response = requests.get(
            f"{BASE_URL}/sessions/",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        print(f"Status: {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print("Response is not JSON") 
        
        if response.status_code == 200:
            print("✓ Successfully retrieved active sessions")
    
    def test_token_refresh(self):
        """Test token refresh"""
        self.print_section("Test 7: Token Refresh")
        
        if not self.refresh_token:
            print("✗ No refresh token available. Login first.")
            return
        
        print(f"Current refresh token: {self.refresh_token[:50]}...")
        
        response = requests.post(
            f"{BASE_URL}/refresh/",
            json={"refresh_token": self.refresh_token}
        )
        
        print(f"\nStatus: {response.status_code}")
        data = response.json()
        try:
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print("Response is not JSON") 
        
        if response.status_code == 200:
            old_refresh = self.refresh_token
            self.access_token = data.get('access')
            self.refresh_token = data.get('refresh')
            print("\n✓ Tokens refreshed successfully!")
            print(f"  New Access Token: {self.access_token[:50]}...")
            print(f"  New Refresh Token: {self.refresh_token[:50]}...")
            
            # Verify old token is revoked
            print("\n  Testing old refresh token (should fail)...")
            response = requests.post(
                f"{BASE_URL}/refresh/",
                json={"refresh_token": old_refresh}
            )
            print(f"  Status: {response.status_code}")
            if response.status_code == 400:
                print("  ✓ Old token correctly revoked (token rotation working)")
    
    def test_logout(self):
        """Test logout"""
        self.print_section("Test 8: Logout")
        
        if not self.access_token or not self.refresh_token:
            print("✗ No tokens available. Login first.")
            return
        
        response = requests.post(
            f"{BASE_URL}/logout/",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"refresh_token": self.refresh_token}
        )
        
        print(f"Status: {response.status_code}")
        # print(f"Response: {json.dumps(response.json(), indent=2)}")
        try:
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print("Response is not JSON") 
            
        if response.status_code == 200:
            print("✓ Logout successful!")
            
            # Try to use the refresh token again (should fail)
            print("\nTrying to use revoked refresh token...")
            response = requests.post(
                f"{BASE_URL}/refresh/",
                json={"refresh_token": self.refresh_token}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 400:
                print("✓ Revoked token correctly rejected")
    
    def run_all_tests(self):
        """Run all authentication tests"""
        print("\n" + "🚀"*30)
        print(" AUTHENTICATION FLOW TESTS")
        print("🚀"*30)
        
        self.create_test_user()
        self.test_login_success()
        self.test_login_invalid_credentials()
        self.test_login_unverified_user()
        self.test_rate_limiting()
        self.test_get_profile()
        self.test_get_active_sessions()
        self.test_token_refresh()
        self.test_logout()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED!")
        print("="*60)


if __name__ == '__main__':
    tester = AuthTester()
    tester.run_all_tests()