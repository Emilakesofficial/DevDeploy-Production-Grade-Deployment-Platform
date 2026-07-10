#!/usr/bin/env python
"""
Test session management
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import requests
import json
from accounts.models import User

BASE_URL = "http://localhost:8000/api/auth"


def test_sessions():
    """Test session management"""
    
    print("\n" + "="*60)
    print("Testing Session Management")
    print("="*60)
    
    # Create test user
    email = "sessiontest@example.com"
    password = "SecurePass123!"
    
    User.objects.filter(email=email).delete()
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name="Session",
        last_name="Test",
        is_active=True,
        is_verified=True
    )
    print(f"\n✓ Created user: {email}")
    
    # Login from "multiple devices" (simulated)
    print("\n1. Logging in from 3 'devices'...")
    sessions = []
    
    for i in range(3):
        response = requests.post(
            f"{BASE_URL}/login/",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            sessions.append({
                'access': data['access'],
                'refresh': data['refresh']
            })
            print(f"   Device {i+1}: ✓ Logged in")
    
    # Get active sessions
    print("\n2. Getting active sessions...")
    response = requests.get(
        f"{BASE_URL}/sessions/",
        headers={"Authorization": f"Bearer {sessions[0]['access']}"}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total sessions: {data['total']}")
    print(f"Sessions: {json.dumps(data['sessions'], indent=2)}")
    
    # Revoke one session
    if data['sessions']:
        session_id = data['sessions'][0]['id']
        print(f"\n3. Revoking session: {session_id}")
        
        response = requests.post(
            f"{BASE_URL}/revoke-session/",
            headers={"Authorization": f"Bearer {sessions[0]['access']}"},
            json={"session_id": session_id}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Revoke all other sessions
    print("\n4. Revoking all other sessions...")
    response = requests.post(
        f"{BASE_URL}/revoke-all-sessions/",
        headers={"Authorization": f"Bearer {sessions[1]['access']}"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Check sessions again
    print("\n5. Checking sessions after revocation...")
    response = requests.get(
        f"{BASE_URL}/sessions/",
        headers={"Authorization": f"Bearer {sessions[1]['access']}"}
    )
    data = response.json()
    print(f"Remaining sessions: {data['total']}")
    
    print("\n" + "="*60)
    print("✅ Session management tests completed!")
    print("="*60)


if __name__ == '__main__':
    test_sessions()