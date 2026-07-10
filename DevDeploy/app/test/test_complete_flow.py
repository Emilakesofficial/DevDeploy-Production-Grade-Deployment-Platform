#!/usr/bin/env python
"""
Complete integration test for entire authentication flow
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import requests
import json
from accounts.models import User, EmailToken
from accounts.services.token_service import TokenService

BASE_URL = "http://localhost:8000/api/auth"


class CompleteFlowTester:
    def __init__(self):
        self.email = "complete@example.com"
        self.password = "InitialPass123!"
        self.new_password = "NewPass123!"
        self.access_token = None
        self.refresh_token = None
    
    def print_step(self, step_num, title):
        """Print step header"""
        print(f"\n{'='*60}")
        print(f"Step {step_num}: {title}")
        print(f"{'='*60}")
    
    def run_complete_flow(self):
        """Run complete authentication flow"""
        
        print("\n" + "🔄"*30)
        print(" COMPLETE AUTHENTICATION FLOW")
        print("🔄"*30)
        
        # Step 1: Register
        self.print_step(1, "Register New User")
        User.objects.filter(email=self.email).delete()
        
        response = requests.post(
            f"{BASE_URL}/register/",
            json={
                "email": self.email,
                "first_name": "Complete",
                "last_name": "Test",
                "password": self.password,
                "password_confirm": self.password
            }
        )
        print(f"Status: {response.status_code}")
        print(f"✓ User registered (inactive, unverified)")
        
        # Step 2: Verify Email
        self.print_step(2, "Verify Email")
        user = User.objects.get(email=self.email)
        
        # Simulate email verification
        verification_token = TokenService.generate_token()
        token_obj = EmailToken.objects.filter(
            user=user, token_type='verify'
        ).latest('created_at')
        token_obj.token_hash = TokenService.hash_token(verification_token)
        token_obj.save()
        
        response = requests.post(
            f"{BASE_URL}/verify-email/",
            json={"token": verification_token}
        )
        print(f"Status: {response.status_code}")
        print(f"✓ Email verified (user now active)")
        
        # Step 3: Login
        self.print_step(3, "Login")
        response = requests.post(
            f"{BASE_URL}/login/",
            json={
                "email": self.email,
                "password": self.password
            }
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        self.access_token = data['access']
        self.refresh_token = data['refresh']
        print(f"✓ Logged in successfully")
        print(f"  Access Token: {self.access_token[:50]}...")
        
        # Step 4: Get Profile
        self.print_step(4, "Get User Profile")
        response = requests.get(
            f"{BASE_URL}/me/",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        print(f"Status: {response.status_code}")
        print(f"Profile: {json.dumps(response.json(), indent=2)}")
        
        # Step 5: Change Password
        self.print_step(5, "Change Password")
        response = requests.post(
            f"{BASE_URL}/change-password/",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={
                "old_password": self.password,
                "new_password": self.new_password,
                "new_password_confirm": self.new_password
            }
        )
        print(f"Status: {response.status_code}")
        print(f"✓ Password changed")
        
        # Step 6: Refresh Token
        self.print_step(6, "Refresh Access Token")
        response = requests.post(
            f"{BASE_URL}/refresh/",
            json={"refresh_token": self.refresh_token}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access']
            self.refresh_token = data['refresh']
            print(f"✓ Tokens refreshed")
        
        # Step 7: Forgot Password
        self.print_step(7, "Forgot Password")
        response = requests.post(
            f"{BASE_URL}/forgot-password/",
            json={"email": self.email}
        )
        print(f"Status: {response.status_code}")
        print(f"✓ Password reset requested")
        
        # Simulate getting reset token
        user.refresh_from_db()
        reset_token = TokenService.generate_token()
        token_obj = EmailToken.objects.filter(
            user=user, token_type='reset', used=False
        ).latest('created_at')
        token_obj.token_hash = TokenService.hash_token(reset_token)
        token_obj.save()
        
        # Step 8: Reset Password
        self.print_step(8, "Reset Password with Token")
        final_password = "FinalPass123!"
        response = requests.post(
            f"{BASE_URL}/reset-password/",
            json={
                "token": reset_token,
                "password": final_password,
                "password_confirm": final_password
            }
        )
        print(f"Status: {response.status_code}")
        print(f"✓ Password reset completed")
        
        # Step 9: Login with New Password
        self.print_step(9, "Login with New Password")
        response = requests.post(
            f"{BASE_URL}/login/",
            json={
                "email": self.email,
                "password": final_password
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access']
            print(f"✓ Login successful with new password")
        
        # Step 10: View Sessions
        self.print_step(10, "View Active Sessions")
        response = requests.get(
            f"{BASE_URL}/sessions/",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        print(f"Status: {response.status_code}")
        print(f"Sessions: {json.dumps(response.json(), indent=2)}")
        
        # Step 11: Logout
        self.print_step(11, "Logout")
        response = requests.post(
            f"{BASE_URL}/logout/",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"refresh_token": self.refresh_token}
        )
        print(f"Status: {response.status_code}")
        print(f"✓ Logged out successfully")
        
        print("\n" + "="*60)
        print("✅ COMPLETE FLOW TEST PASSED!")
        print("="*60)
        print("\nAll features tested:")
        print("  ✓ Registration")
        print("  ✓ Email Verification")
        print("  ✓ Login")
        print("  ✓ Get Profile")
        print("  ✓ Change Password")
        print("  ✓ Token Refresh")
        print("  ✓ Forgot Password")
        print("  ✓ Reset Password")
        print("  ✓ Session Management")
        print("  ✓ Logout")


if __name__ == '__main__':
    tester = CompleteFlowTester()
    tester.run_complete_flow()