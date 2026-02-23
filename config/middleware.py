"""Custom middleware for TUS website."""
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import http_date


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


class CacheControlMiddleware(MiddlewareMixin):
    """Middleware that sets proper Cache-Control headers for SEO freshness.

    Problem: Without explicit cache directives, browsers and Googlebot may
    serve stale versions of pages indefinitely after a deploy.

    Strategy:
    - HTML pages: ``no-cache`` (always revalidate with server before showing)
      with ``must-revalidate`` so proxies don't serve stale content.
    - Static files: left to WhiteNoise (which handles them before Django).
    - Admin pages: ``no-store`` to never cache sensitive data.
    - Also sets ``Last-Modified`` so Googlebot can send conditional requests
      (``If-Modified-Since``) and get fast 304 responses.
    """

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        # Skip if Cache-Control is already set (e.g. by WhiteNoise or a view)
        if 'Cache-Control' in response:
            return response

        content_type = response.get('Content-Type', '')

        # Admin/private pages: never cache
        if request.path.startswith(('/tus-gestion-secure/', '/ecosysteme-tus/', '/accounts/')):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            return response

        # HTML pages: allow caching but force revalidation on every visit
        # Googlebot will fetch a fresh copy and index new content immediately
        if 'text/html' in content_type:
            response['Cache-Control'] = 'no-cache, must-revalidate'
            # Add Last-Modified so Googlebot can do conditional requests (304)
            if 'Last-Modified' not in response:
                response['Last-Modified'] = http_date(time.time())
            return response

        # API / JSON responses: short cache
        if 'application/json' in content_type:
            response['Cache-Control'] = 'no-cache, must-revalidate'
            return response

        return response