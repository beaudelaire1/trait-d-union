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
    les soumissions POST sur /contact/ par IP dans une fenêtre glissante.
    Compatible multi-workers gunicorn.
    """

    RATE_LIMIT: int = 5
    WINDOW_SECONDS: int = 3600

    def process_request(self, request: HttpRequest) -> None | HttpResponse:
        if not request.path.startswith('/contact/') or request.method != 'POST':
            return None

        ip = request.META.get('REMOTE_ADDR', '')
        cache_key = f"ratelimit:contact:{ip}"

        current = cache.get(cache_key, 0)
        if current >= self.RATE_LIMIT:
            response = HttpResponse('Too Many Requests', status=429)
            response['Retry-After'] = str(self.WINDOW_SECONDS)
            return response

        # incr() est atomique dans les backends Redis/memcached
        try:
            cache.incr(cache_key)
        except ValueError:
            # Clé n'existe pas encore → la créer avec TTL
            cache.set(cache_key, 1, self.WINDOW_SECONDS)

        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware that adds security-related HTTP headers."""

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        response.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('Referrer-Policy', 'same-origin')

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
