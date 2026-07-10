"""Development settings"""

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Development-specific settings
EMAIL_BACKEND = config('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')

# CORS - Allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# Security settings - relaxed for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False