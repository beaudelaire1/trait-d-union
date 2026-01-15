"""Custom middleware for TUS website."""
import time
from collections import defaultdict
from typing import Any, Callable

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin


class RateLimitMiddleware(MiddlewareMixin):
    """Simple rate limiting middleware (naïve, in-memory).

    Limits the number of requests per IP address over a sliding window.  The
    specification requires limiting contact form submissions to 5 per hour
    (Property 5).  This implementation uses an in‑memory dictionary of
    timestamps keyed by IP.  It is suitable for development only; in
    production a distributed store (Redis) should be used.
    """

    #: Maximum number of allowed requests per IP within the window
    RATE_LIMIT: int = 5
    #: Length of the time window in seconds (60 minutes)
    WINDOW_SECONDS: int = 3600
    #: Internal registry mapping IP addresses to a list of request
    #: timestamps.  The defaultdict avoids key errors when an IP is
    #: encountered for the first time.
    _requests: defaultdict[str, list[float]] = defaultdict(list)

    def process_request(self, request: HttpRequest) -> None | HttpResponse:
        # Only apply rate limiting to contact form POST requests
        if not request.path.startswith('/contact/') or request.method != 'POST':
            return None

        ip = request.META.get('REMOTE_ADDR', '')
        now = time.time()
        window_start = now - self.WINDOW_SECONDS
        # Remove timestamps outside the sliding window
        self._requests[ip] = [ts for ts in self._requests[ip] if ts > window_start]
        if len(self._requests[ip]) >= self.RATE_LIMIT:
            # Too many submissions: return HTTP 429 with retry header
            response = HttpResponse('Too Many Requests', status=429)
            response['Retry-After'] = str(self.WINDOW_SECONDS)
            return response
        # Record current request timestamp and continue processing
        self._requests[ip].append(now)
        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware that adds security-related HTTP headers."""

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        response.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('Referrer-Policy', 'same-origin')
        response.setdefault('X-XSS-Protection', '1; mode=block')
        return response