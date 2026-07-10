#!/usr/bin/env python
"""
Security configuration checklist
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings


def check_security():
    """Run security checks"""
    
    print("\n" + "🔒"*30)
    print(" SECURITY CONFIGURATION CHECK")
    print("🔒"*30 + "\n")
    
    issues = []
    passed = []
    
    # Check DEBUG setting
    if settings.DEBUG:
        issues.append("❌ DEBUG is True (should be False in production)")
    else:
        passed.append("✅ DEBUG is False")
    
    # Check SECRET_KEY
    if settings.SECRET_KEY == 'your-secret-key-here-change-in-production':
        issues.append("❌ SECRET_KEY is default value (change in production)")
    else:
        passed.append("✅ SECRET_KEY is set")
    
    # Check ALLOWED_HOSTS
    if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
        issues.append("❌ ALLOWED_HOSTS not properly configured")
    else:
        passed.append("✅ ALLOWED_HOSTS is configured")
    
    # Check HTTPS settings
    if hasattr(settings, 'SECURE_SSL_REDIRECT'):
        if settings.SECURE_SSL_REDIRECT:
            passed.append("✅ SECURE_SSL_REDIRECT is True")
        else:
            issues.append("⚠️  SECURE_SSL_REDIRECT is False")
    
    # Check session security
    if hasattr(settings, 'SESSION_COOKIE_SECURE'):
        if settings.SESSION_COOKIE_SECURE:
            passed.append("✅ SESSION_COOKIE_SECURE is True")
        else:
            issues.append("⚠️  SESSION_COOKIE_SECURE is False")
    
    # Check CSRF security
    if hasattr(settings, 'CSRF_COOKIE_SECURE'):
        if settings.CSRF_COOKIE_SECURE:
            passed.append("✅ CSRF_COOKIE_SECURE is True")
        else:
            issues.append("⚠️  CSRF_COOKIE_SECURE is False")
    
    # Check password hashers
    if 'Argon2PasswordHasher' in str(settings.PASSWORD_HASHERS[0]):
        passed.append("✅ Using Argon2 for password hashing")
    else:
        issues.append("⚠️  Not using Argon2 as primary password hasher")
    
    # Check email configuration
    if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
        passed.append("✅ Email is configured")
    else:
        issues.append("⚠️  Email not fully configured")
    
    # Print results
    print("PASSED CHECKS:")
    for item in passed:
        print(f"  {item}")
    
    if issues:
        print("\nISSUES FOUND:")
        for item in issues:
            print(f"  {item}")
    
    print("\n" + "="*60)
    print(f"Total: {len(passed)} passed, {len(issues)} issues")
    print("="*60 + "\n")


if __name__ == '__main__':
    check_security()