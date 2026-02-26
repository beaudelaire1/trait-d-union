"""Custom middleware for TUS website."""
import time
from typing import Any, Callable

from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import http_date


class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting via Django cache backend (multi-process safe).

    Utilise le cache Django (Redis en prod, LocMem en dev) pour compter
    les soumissions POST par IP dans une fenêtre glissante.
    Compatible multi-workers gunicorn.

    Routes protégées :
    - /contact/          → 5 req/heure (anti-spam formulaire)
    - /accounts/login/   → 10 req/heure (anti brute-force)
    - /accounts/signup/  → 5 req/heure (anti création de masse)
    """

    # (path_prefix, max_requests, window_seconds)
    RATE_LIMITS: list[tuple[str, int, int]] = [
        ('/contact/', 5, 3600),
        ('/accounts/login/', 10, 3600),
        ('/accounts/signup/', 5, 3600),
    ]

    def process_request(self, request: HttpRequest) -> None | HttpResponse:
        if request.method != 'POST':
            return None

        for path_prefix, max_requests, window_seconds in self.RATE_LIMITS:
            if request.path.startswith(path_prefix):
                return self._check_rate(request, path_prefix, max_requests, window_seconds)

        return None

    def _check_rate(
        self,
        request: HttpRequest,
        path_prefix: str,
        max_requests: int,
        window_seconds: int,
    ) -> None | HttpResponse:
        """Check and enforce rate limit for a given route."""
        ip = request.META.get('REMOTE_ADDR', '')
        # Normalise le path prefix pour la clé cache (ex: "contact", "login")
        route_key = path_prefix.strip('/').replace('/', '_')
        cache_key = f"ratelimit:{route_key}:{ip}"

        current = cache.get(cache_key, 0)
        if current >= max_requests:
            response = HttpResponse('Too Many Requests', status=429)
            response['Retry-After'] = str(window_seconds)
            return response

        # incr() est atomique dans les backends Redis/memcached
        try:
            cache.incr(cache_key)
        except ValueError:
            # Clé n'existe pas encore → la créer avec TTL
            cache.set(cache_key, 1, window_seconds)

        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware that adds security-related HTTP headers including CSP."""

    # Content-Security-Policy directives.
    # Kept as a class attribute for easy override in tests / settings.
    CSP_DIRECTIVES = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com "
        "https://www.googletagmanager.com https://www.google-analytics.com "
        "https://challenges.cloudflare.com https://www.google.com https://www.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: blob: https://res.cloudinary.com https://www.google-analytics.com https://*.stripe.com; "
        "connect-src 'self' https://www.google-analytics.com https://challenges.cloudflare.com https://api.stripe.com; "
        "frame-src https://challenges.cloudflare.com https://www.google.com https://js.stripe.com; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self' https://checkout.stripe.com"
    )

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        response.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')

        # Content-Security-Policy
        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = self.CSP_DIRECTIVES

        # Permissions-Policy (anciennement Feature-Policy)
        from django.conf import settings
        permissions = getattr(settings, 'PERMISSIONS_POLICY', None)
        if permissions and 'Permissions-Policy' not in response:
            directives = []
            for feature, origins in permissions.items():
                if not origins:
                    directives.append(f'{feature}=()')
                elif origins == ['self']:
                    directives.append(f'{feature}=(self)')
                else:
                    allowed = ' '.join(f'"{o}"' for o in origins)
                    directives.append(f'{feature}=({allowed})')
            response['Permissions-Policy'] = ', '.join(directives)

        return response


class CacheControlMiddleware(MiddlewareMixin):
    """Middleware that sets proper Cache-Control headers for SEO freshness.

    Strategy:
    - HTML pages: ``no-cache`` (always revalidate with server before showing)
    - Admin pages: ``no-store`` to never cache sensitive data.
    - Sets ``Last-Modified`` so Googlebot can send conditional requests.
    """

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        if 'Cache-Control' in response:
            return response

        content_type = response.get('Content-Type', '')

        if request.path.startswith(('/tus-gestion-secure/', '/ecosysteme-tus/', '/accounts/')):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            return response

        if 'text/html' in content_type:
            response['Cache-Control'] = 'no-cache, must-revalidate'
            if 'Last-Modified' not in response:
                response['Last-Modified'] = http_date(time.time())
            return response

        if 'application/json' in content_type:
            response['Cache-Control'] = 'no-cache, must-revalidate'
            return response

        return response
