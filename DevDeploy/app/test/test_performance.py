#!/usr/bin/env python
"""
Performance test for authentication endpoints
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import requests
import time
from concurrent.futures import ThreadPoolExecutor
from accounts.models import User

BASE_URL = "http://localhost:8000/api/auth"


def create_test_users(count=10):
    """Create multiple test users"""
    print(f"Creating {count} test users...")
    users = []
    
    for i in range(count):
        email = f"perftest{i}@example.com"
        User.objects.filter(email=email).delete()
        user = User.objects.create_user(
            email=email,
            password="SecurePass123!",
            first_name="Perf",
            last_name=f"Test{i}",
            is_active=True,
            is_verified=True
        )
        users.append(user)
    
    print(f"✓ Created {len(users)} users")
    return users


def login_user(user_index):
    """Login a single user"""
    email = f"perftest{user_index}@example.com"
    start_time = time.time()
    
    response = requests.post(
        f"{BASE_URL}/login/",
        json={"email": email, "password": "SecurePass123!"}
    )
    
    duration = time.time() - start_time
    return {
        'status': response.status_code,
        'duration': duration,
        'success': response.status_code == 200
    }


def test_concurrent_logins(user_count=10):
    """Test concurrent logins"""
    print(f"\nTesting {user_count} concurrent logins...")
    
    with ThreadPoolExecutor(max_workers=user_count) as executor:
        start_time = time.time()
        results = list(executor.map(login_user, range(user_count)))
        total_duration = time.time() - start_time
    
    successful = sum(1 for r in results if r['success'])
    avg_duration = sum(r['duration'] for r in results) / len(results)
    
    print(f"\nResults:")
    print(f"  Total time: {total_duration:.2f}s")
    print(f"  Successful logins: {successful}/{user_count}")
    print(f"  Average response time: {avg_duration:.3f}s")
    print(f"  Requests per second: {user_count/total_duration:.2f}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Performance Testing")
    print("="*60)
    
    users = create_test_users(20)
    test_concurrent_logins(20)
    
    print("\n" + "="*60)
    print("✅ Performance tests completed!")
    print("="*60)