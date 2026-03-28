"""Custom middleware for TUS website."""
import logging
import time
from typing import Any, Callable

from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import http_date

logger = logging.getLogger(__name__)


# 🛡️ SECURITY: Single source of truth for IP extraction (DRY)
from core.utils import get_client_ip as _get_client_ip  # noqa: E402


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
        ('/devis/', 5, 3600),
        ('/devis/pdf/', 20, 3600),  # 🛡️ Rate limit public PDF downloads (GET)
        ('/factures/payer/', 10, 3600),  # 🛡️ Rate limit public invoice payment page
        ('/factures/webhook/', 60, 60),  # 🛡️ Rate limit Stripe webhooks (60/min)
        ('/tus-gestion-secure/login/', 5, 900),  # 🛡️ Admin login: 5 attempts / 15 min
    ]

    # Routes also rate-limited on GET (e.g. public PDF downloads)
    GET_RATE_LIMITS: list[tuple[str, int, int]] = [
        ('/devis/pdf/', 20, 3600),
        ('/factures/pdf/', 20, 3600),  # 🛡️ Rate limit public invoice PDF downloads
    ]

    def process_request(self, request: HttpRequest) -> None | HttpResponse:
        # Rate-limit GET on specific routes
        if request.method == 'GET':
            for path_prefix, max_requests, window_seconds in self.GET_RATE_LIMITS:
                if request.path.startswith(path_prefix):
                    return self._check_rate(request, path_prefix, max_requests, window_seconds)

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
        """Check and enforce rate limit for a given route.

        🛡️ SECURITY: If the cache backend is unavailable (Redis down),
        fail-open to avoid blocking legitimate traffic.  The Stripe
        webhook signature and Django CSRF still protect against abuse.
        Rate limiting is a *defense-in-depth* layer, not the sole gate.
        """
        # 🛡️ SECURITY: Sanitized IP extraction (see _get_client_ip)
        ip = _get_client_ip(request)
        # Normalise le path prefix pour la clé cache (ex: "contact", "login")
        route_key = path_prefix.strip('/').replace('/', '_')
        cache_key = f"ratelimit:{route_key}:{ip}"

        try:
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
        except Exception:
            # 🛡️ SECURITY: Cache backend unavailable (Redis down) — fail-closed
            # for sensitive routes, fail-open for everything else.
            import logging
            _logger = logging.getLogger('config.middleware')
            _logger.warning(
                "Rate limit cache unavailable for %s — applying in-memory fallback", route_key
            )
            # Fail-closed on login / contact / signup (block if cache down)
            _SENSITIVE_ROUTES = {'contact', 'accounts_login', 'accounts_signup', 'tus-gestion-secure_login'}
            if route_key in _SENSITIVE_ROUTES:
                response = HttpResponse('Service temporarily unavailable', status=503)
                response['Retry-After'] = '30'
                return response

        return None



# NOTE: SecurityHeadersMiddleware has been REMOVED (was dead code).
# All security headers are now handled by:
#   - django-csp (csp.middleware.CSPMiddleware) for CSP
#   - Django's SecurityMiddleware for X-Content-Type-Options, HSTS, etc.
#   - Permissions-Policy is set via PERMISSIONS_POLICY dict in settings


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
            # 🛡️ SECURITY: Prevent search engines from indexing admin/portal pages
            response['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
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


class SecurityAuditMiddleware(MiddlewareMixin):
    """🛡️ BANK-GRADE: Log security events to AuditLog for SIEM correlation.

    Captures:
    - Failed login attempts (401/403 on login endpoints)
    - Rate limit hits (429 responses)
    - Suspicious patterns (path traversal, SQL injection probes)
    """

    _SUSPICIOUS_PATTERNS = (
        '../', '..\\', '%2e%2e', 'union+select', 'union%20select',
        '<script', '%3cscript', 'javascript:', 'onerror=', 'onload=',
        '.php', 'wp-admin', 'wp-login', '.env', '.git/',
    )

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        # Log rate limit hits
        if response.status_code == 429:
            self._log_security_event(
                request, 'rate_limit_hit',
                f"Rate limit 429 on {request.method} {request.path}",
            )

        # Log failed login attempts
        if (
            response.status_code in (401, 403)
            and request.path.startswith(('/accounts/login/', '/tus-gestion-secure/login/'))
            and request.method == 'POST'
        ):
            self._log_security_event(
                request, 'login_failed',
                f"Failed login attempt on {request.path}",
            )

        # Log suspicious path patterns
        path_lower = request.path.lower()
        query_lower = request.META.get('QUERY_STRING', '').lower()
        combined = path_lower + query_lower
        for pattern in self._SUSPICIOUS_PATTERNS:
            if pattern in combined:
                self._log_security_event(
                    request, 'suspicious_activity',
                    f"Suspicious pattern '{pattern}' in {request.method} {request.path}",
                )
                break

        return response

    def _log_security_event(self, request: HttpRequest, action_type: str, description: str):
        """Best-effort async security event logging."""
        try:
            from apps.audit.models import AuditLog
            ip = _get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            AuditLog.log_action(
                action_type=action_type,
                actor=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
                content_type='security.event',
                object_id=0,
                description=description,
                metadata={
                    'ip': ip,
                    'user_agent': user_agent,
                    'path': request.path[:500],
                    'method': request.method,
                },
            )
        except Exception:
            # Never break the request pipeline for audit logging
            logger.warning("Failed to log security event: %s", description)


class CanonicalDomainMiddleware(MiddlewareMixin):
    """🔍 SEO: Redirect non-canonical hosts to canonical domain.

    Prevents duplicate content penalties from Google by enforcing a single
    canonical domain. Only active when CANONICAL_DOMAIN is set (production).

    Redirects:
    - traitdunion.it → www.traitdunion.it (301) when CANONICAL_DOMAIN=www.traitdunion.it
    - trait-d-union.onrender.com → www.traitdunion.it (301)

    Protection anti-boucle :
    - Un cookie ``_canonical_ok`` est posé lors du redirect.
    - Si le cookie est présent sur une requête qui devrait être redirigée,
      cela signifie que la redirection précédente n'a pas atteint le bon
      domaine (boucle entre Render/CDN et Django).  On sert la page sans
      rediriger et on log un warning.
    - Le cookie est court (max_age=30 s) pour ne pas masquer un vrai besoin
      de redirection une fois la configuration corrigée.
    """

    # Paths excluded from canonical redirect (health checks, static, media)
    EXEMPT_PREFIXES = ('/healthz/', '/static/', '/media/')

    # Cookie used to detect redirect loops
    _LOOP_COOKIE = '_canonical_ok'

    def process_request(self, request: HttpRequest) -> HttpResponse | None:
        from django.conf import settings

        canonical = getattr(settings, 'CANONICAL_DOMAIN', '')
        if not canonical:
            return None

        # Skip health checks, static files and media (Render probes, WhiteNoise)
        for prefix in self.EXEMPT_PREFIXES:
            if request.path.startswith(prefix):
                return None

        host = request.get_host().split(':')[0].lower()  # Strip port, case-insensitive

        # Already on canonical domain → nothing to do
        if host == canonical:
            return None

        # Redirect loop detection: if the browser already carries our loop-
        # detection cookie, it means a previous redirect bounced back here
        # (e.g. Render CDN re-routes the canonical domain to .onrender.com).
        # Breaking the loop avoids ERR_TOO_MANY_REDIRECTS.
        if request.COOKIES.get(self._LOOP_COOKIE):
            logger.warning(
                "Canonical redirect loop detected (host=%s, canonical=%s). "
                "Check Render custom-domain configuration and DNS records.",
                host, canonical,
            )
            return None

        # Build redirect URL — determine scheme properly
        if request.is_secure():
            scheme = 'https'
        else:
            # Behind Render/proxy, request may appear as HTTP even for HTTPS
            # traffic.  Trust X-Forwarded-Proto when SECURE_PROXY_SSL_HEADER
            # is configured (Django already handles this via is_secure()).
            # Fallback to https in production as a safe default.
            scheme = 'https'

        from django.http import HttpResponsePermanentRedirect
        new_url = f"{scheme}://{canonical}{request.get_full_path()}"
        response = HttpResponsePermanentRedirect(new_url)

        # Set a short-lived cookie so the next request can detect a loop.
        # SameSite=Lax ensures the cookie is sent on top-level navigations.
        response.set_cookie(
            self._LOOP_COOKIE, '1',
            max_age=30,
            httponly=True,
            samesite='Lax',
            secure=getattr(settings, 'SESSION_COOKIE_SECURE', False),
        )
        return response
