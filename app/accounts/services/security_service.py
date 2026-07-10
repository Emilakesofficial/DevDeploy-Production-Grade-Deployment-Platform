import logging
import re 
from django.core.cache import cache
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from audit.models import AuditLog

logger = logging.getLogger(__name__)

class SecurityService:
    # Rate limit settings
    MAX_LOGIN_ATTEMPTS = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)
    LOGIN_LOCKOUT_DURATION = getattr(settings, 'LOGIN_LOGOUT_DURATION_MINUTES', 15)
    
    # Cache key templates
    LOGIN_ATTEMPTS_KEY = 'login_attempts:{}'
    LOGIN_BLOCK_KEY = 'login_block:{}'
    IP_ATTEMPTS_KEY = 'ip_attempts:{}'
    
    # Password validation regex
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REGEX = {
        'uppercase': re.compile(r'[A-Z]'),
        'lowercase': re.compile(r'[a-z]'),
        'digit': re.compile(r'\d'),
        'special': re.compile(r'[!@#$%^&*(),.?":{}|<>]'),
    }
    
    @classmethod
    def validate_password_strength(cls, password):
        """Validate password strength"""
        
        if len(password) < cls.PASSWORD_MIN_LENGTH:
            return False, f'Password must be at least {cls.PASSWORD_MIN_LENGTH} characters long'
        
        if not cls.PASSWORD_REGEX['uppercase'].search(password):
            return False, 'Password must contain at least one uppercase letter'
        
        if not cls.PASSWORD_REGEX['lowercase'].search(password):
            return False, 'Password must contain at least one lowercase letter'
        
        if not cls.PASSWORD_REGEX['digit'].search(password):
            return False, 'Password must contain at least one digit'
        
        if not cls.PASSWORD_REGEX['special'].search(password):
            return False, 'Password must contain at least one special character'
        
        return True, None
    
    @classmethod
    def check_login_attempts(cls, email):
        """Check if a user is locked out due to failed login attempts"""
        block_key = cls.LOGIN_BLOCK_KEY.format(email)
        
        # check if user is currently blocked
        if cache.get(block_key):
            ttl = cache.ttl(block_key)
            return True, cls.MAX_LOGIN_ATTEMPTS, ttl
        
        # Get current attempt count
        attempts_key = cls.LOGIN_ATTEMPTS_KEY.format(email)
        attempts = cache.get(attempts_key, 0)
        
        return False, attempts, 0
    
    @classmethod
    def record_failed_login(cls, email, ip_address):
        """Record a failed login attempt"""
        email = email.lower()
        attempts_key = cls.LOGIN_ATTEMPTS_KEY.format(email)
        
        # increment attempt counter
        attempts = cache.get(attempts_key, 0) + 1
        cache.set(attempts_key, attempts, timeout=3600)
        
        # Track by IP
        ip_key = cls.IP_ATTEMPTS_KEY.format(ip_address)
        ip_count = cache.get(ip_key, 0) + 1
        cache.set(ip_key, ip_count, timeout=3600)
        
        logger.warning(
            f"Failed login attempt",
            extra={
                'email': email,
                'ip_address': ip_address,
                'attempt_number': attempts,
                'max_attempts': cls.MAX_LOGIN_ATTEMPTS
            }
        )
        
        # Lock account if threshold exceeded
        if attempts >= cls.MAX_LOGIN_ATTEMPTS:
            block_key = cls.LOGIN_BLOCK_KEY.format(email)
            lockout_seconds = cls.LOGIN_LOCKOUT_DURATION * 60
            cache.set(block_key, True, timeout=lockout_seconds)
            logger.warning(
                f"Account locked",
                extra={
                    'email': email,
                    'ip_address': ip_address,
                    'lockout_minutes': cls.LOGIN_LOCKOUT_DURATION
                }
            )

            return True, 0
        return False, cls.MAX_LOGIN_ATTEMPTS - attempts
    
    @classmethod
    def reset_login_attempts(cls, email, ip_address=None):
        """Reset login attempts after successful login"""
        email = email.lower()
        attempts_key = cls.LOGIN_ATTEMPTS_KEY.format(email)
        block_key = cls.LOGIN_BLOCK_KEY.format(email)
        
        cache.delete(attempts_key)
        cache.delete(block_key)
        
        logger.info(f"Login attempts reset for {email}")
        
    @classmethod
    def clear_user_lockout(cls, email):
        """
        Manually clear lockout for a user (admin use)
        Uses Django cache — handles prefix automatically
        """
        email = email.lower()
        attempts_key = cls.LOGIN_ATTEMPTS_KEY.format(email)
        block_key = cls.LOGIN_BLOCK_KEY.format(email)

        cache.delete(attempts_key)
        cache.delete(block_key)

        logger.info(f"Manually cleared lockout for {email}")
        return True
        
    @classmethod
    def check_suspicious_activity(cls, user, ip_address, user_agent):
        """Check for suspicious activity, return(is_suspicious, reason)"""
        
        ip_key = cls.IP_ATTEMPTS_KEY.format(ip_address)
        ip_attempts = cache.get(ip_key, 0)
        
        if ip_attempts > 20:
            return True, 'Too many attempts from this IP address'
        
        # Get user's recent login from audit logs
        recent_logins = AuditLog.objects.filter(
            user=user,
            action='login_success',
            timestamp__gte=timezone.now() - timedelta(days=30)
        ).order_by('-timestamp')[:10]
        
        
        # check if this is a new IP
        known_ips = set(log.ip_address for log in recent_logins)
        if known_ips and ip_address not in known_ips:
            return True, 'Login from new IP address'
        return False, None
    
    @classmethod
    def get_client_ip(cls, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @classmethod
    def get_user_agent(cls, request):
        """Extract user agent from request"""
        return request.META.get('HTTP_USER_AGENT', '')
    
    @classmethod
    def get_device_info(cls, request):
        """Extract basic device info from request"""
        user_agent = cls.get_user_agent(request)
        # Basic device detection (can be enhanced with a library like user-agents)
        if 'Mobile' in user_agent:
            device_type = 'Mobile'
        elif 'Tablet' in user_agent:
            device_type = 'Tablet'
        else:
            device_type = 'Desktop'
            
        return f"{device_type} - {user_agent[:50]}"  # Limit user agent length for storage
        