"""
Audit middleware for tracking requests
"""
import uuid
import logging
from django.utils.deprecation import MiddlewareMixin
from accounts.services.security_service import SecurityService

logger = logging.getLogger(__name__)

SKIP_PATHS = [
    '/static/',
    '/media/',
    '/favicon.ico',
    '/nginx-health',
    '/api/auth/health/',
    '/api/schema/',
    '/api/docs/',
    '/api/redoc/',
]

RELAXED_CSP_PATHS = [
    '/api/docs/',
    '/api/redoc/',
    '/api/schema/',
]

class RequestIDMiddleware(MiddlewareMixin):
    """Add unique request ID to each request for tracing"""

    def process_request(self, request):
        request.request_id = str(uuid.uuid4())
        return None

    def process_response(self, request, response):
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id
        return response


class AuditMiddleware(MiddlewareMixin):
    """Log all requests for audit purposes"""

    def _get_user(self, request):
        try:
            if hasattr(request, 'user') and request.user.is_authenticated:
                return str(request.user)
        except Exception:
            pass
        return 'Anonymous'

    def process_request(self, request):
        if any(request.path.startswith(p) for p in SKIP_PATHS):
            return None

        request_id = getattr(request, 'request_id', 'unknown')
        ip_address = SecurityService.get_client_ip(request)

        logger.info(
            "Request started",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.path,
                'ip_address': ip_address,
            }
        )
        return None

    def process_response(self, request, response):
        if any(request.path.startswith(p) for p in SKIP_PATHS):
            return response

        request_id = getattr(request, 'request_id', 'unknown')

        logger.info(
            "Request completed",
            extra={
                'request_id': request_id,
                'status_code': response.status_code,
                'user': self._get_user(request),
            }
        )
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to all responses"""

    def process_response(self, request, response):
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Relaxed CSP for Swagger UI and ReDoc pages
        if any(request.path.startswith(p) for p in RELAXED_CSP_PATHS):
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net unpkg.com; "
                "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net unpkg.com fonts.googleapis.com; "
                "font-src 'self' fonts.gstatic.com; "
                "img-src 'self' data:; "
                "connect-src 'self';"
            )
        else:
            # Strict CSP for all other endpoints
            response['Content-Security-Policy'] = "default-src 'self'"

        return response
