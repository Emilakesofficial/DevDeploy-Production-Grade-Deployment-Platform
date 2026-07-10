from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from accounts.services.security_service import SecurityService

# Paths completely exempt from rate limiting
EXEMPT_PATHS = [
    '/api/auth/health/',
    '/api/schema/',
    '/api/docs/',
    '/api/redoc/',
    '/admin/',
    '/static/',
    '/media/',
    '/nginx-health',
]


class GlobalRateLimitMiddleware(MiddlewareMixin):
    """Global rate limiting for all API endpoints"""

    RATE_LIMIT = 60   # requests
    WINDOW = 60       # seconds

    def process_request(self, request):
        """Check rate limit before processing request"""

        # Skip exempt paths
        if any(request.path.startswith(path) for path in EXEMPT_PATHS):
            return None

        ip_address = SecurityService.get_client_ip(request)
        cache_key = f'rate_limit:{ip_address}'

        requests_count = cache.get(cache_key, 0)

        if requests_count >= self.RATE_LIMIT:
            return JsonResponse(
                {
                    'error': 'Rate limit exceeded. Please try again later.',
                    'detail': f'Maximum {self.RATE_LIMIT} requests per minute allowed.'
                },
                status=429
            )

        cache.set(cache_key, requests_count + 1, timeout=self.WINDOW)
        return None