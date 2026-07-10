"""
Production settings
"""
from .base import *

DEBUG = False

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='*',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Trust the ALB - it handles SSL termination
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# Security Settings
SECURE_SSL_REDIRECT = False  # ALB handles this

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS - Enable ONLY after you have a domain + SSL cert
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# Logging - Use JSON formatter in production
LOGGING['handlers']['console']['formatter'] = 'json'
LOGGING['handlers']['file']['formatter'] = 'json'