#!/usr/bin/env python
"""
Test script for registration flow
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/auth"


def test_registration():
    """Test user registration"""
    print("\n" + "="*60)
    print("Testing User Registration Flow")
    print("="*60)
    
    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 2: Register User
    print("\n2. Testing User Registration...")
    user_data = {
        "email": "testuser@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!"
    }
    
    response = requests.post(f"{BASE_URL}/register/", json=user_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 3: Try registering with same email (should fail)
    print("\n3. Testing Duplicate Email...")
    response = requests.post(f"{BASE_URL}/register/", json=user_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 4: Test weak password
    print("\n4. Testing Weak Password...")
    weak_user_data = {
        "email": "weakpass@example.com",
        "first_name": "Weak",
        "last_name": "Password",
        "password": "weak",
        "password_confirm": "weak"
    }
    
    response = requests.post(f"{BASE_URL}/register/", json=weak_user_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 5: Test password mismatch
    print("\n5. Testing Password Mismatch...")
    mismatch_data = {
        "email": "mismatch@example.com",
        "first_name": "Mismatch",
        "last_name": "User",
        "password": "SecurePass123!",
        "password_confirm": "DifferentPass123!"
    }
    
    response = requests.post(f"{BASE_URL}/register/", json=mismatch_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 6: Resend verification
    print("\n6. Testing Resend Verification...")
    resend_data = {"email": "testuser@example.com"}
    response = requests.post(f"{BASE_URL}/resend-verification/", json=resend_data)
    print("Status:", response.status_code)
    print("Raw response:", response.text)

    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print("Response is not JSON") 
          
    print("\n" + "="*60)
    print("✅ Registration tests completed!")
    print("="*60)
    print("\nNOTE: Check your email inbox for verification emails")
    print("Check Celery worker logs to see email task execution")


if __name__ == '__main__':
    test_registration()