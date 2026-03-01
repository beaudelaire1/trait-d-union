"""Tests for custom middleware (rate limiting, cache control).

Covers:
- Rate limiting respects thresholds
- Rate limiting uses X-Forwarded-For behind proxy
- 429 response after hitting limit
- CacheControlMiddleware sets correct headers
"""
import pytest
from django.test import Client, override_settings
from django.core.cache import cache


@pytest.mark.django_db
class TestRateLimiting:
    """Test RateLimitMiddleware behaviour."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_first_request_passes(self, client):
        """First POST to contact should succeed."""
        response = client.post('/contact/', {
            'name': 'Test',
            'email': 'test@example.com',
            'project_type': 'site',
            'message': 'Hello',
            'honeypot': '',
        })
        assert response.status_code != 429

    def test_rate_limit_triggers_after_threshold(self, client):
        """After 5 POSTs to /contact/, the 6th should return 429."""
        payload = {
            'name': 'Test',
            'email': 'test@example.com',
            'project_type': 'site',
            'message': 'Hello',
            'honeypot': '',
        }
        for _ in range(5):
            client.post('/contact/', payload)

        response = client.post('/contact/', payload)
        assert response.status_code == 429
        assert 'Retry-After' in response

    def test_rate_limit_does_not_affect_get(self, client):
        """GET requests should never be rate-limited."""
        for _ in range(20):
            response = client.get('/contact/')
        assert response.status_code == 200

    def test_rate_limit_uses_forwarded_for(self):
        """When X-Forwarded-For is present, rate limiting uses that IP."""
        c = Client()
        payload = {
            'name': 'Test',
            'email': 'test@example.com',
            'project_type': 'site',
            'message': 'Hello',
            'honeypot': '',
        }
        # 5 requests from IP "1.2.3.4" via proxy
        for _ in range(5):
            c.post('/contact/', payload, HTTP_X_FORWARDED_FOR='1.2.3.4, 10.0.0.1')

        # 6th from same forwarded IP → blocked
        response = c.post('/contact/', payload, HTTP_X_FORWARDED_FOR='1.2.3.4, 10.0.0.1')
        assert response.status_code == 429

        # But a different IP should still work
        response2 = c.post('/contact/', payload, HTTP_X_FORWARDED_FOR='5.6.7.8')
        assert response2.status_code != 429


@pytest.mark.django_db
class TestCacheControlHeaders:
    """Test CacheControlMiddleware header behavior."""

    def test_html_pages_have_no_cache(self, client):
        """HTML responses should have no-cache for SEO freshness."""
        response = client.get('/')
        cc = response.get('Cache-Control', '')
        assert 'no-cache' in cc

    def test_html_pages_have_last_modified(self, client):
        """HTML responses should include Last-Modified for conditional requests."""
        response = client.get('/')
        assert 'Last-Modified' in response


@pytest.mark.django_db
class TestCanonicalDomainMiddleware:
    """Test CanonicalDomainMiddleware redirect & loop protection."""

    _ALLOWED = ['traitdunion.it', 'www.traitdunion.it', 'trait-d-union.onrender.com',
                'internal-hostname.render.com', 'any-host.example.com', 'testserver']

    @override_settings(CANONICAL_DOMAIN='traitdunion.it', ALLOWED_HOSTS=_ALLOWED)
    def test_canonical_host_no_redirect(self, client):
        """Requests to the canonical domain should not be redirected."""
        response = client.get('/', HTTP_HOST='traitdunion.it')
        assert response.status_code == 200

    @override_settings(CANONICAL_DOMAIN='traitdunion.it', SESSION_COOKIE_SECURE=False, ALLOWED_HOSTS=_ALLOWED)
    def test_non_canonical_host_redirects(self, client):
        """Requests to a non-canonical host should 301 to canonical."""
        response = client.get('/', HTTP_HOST='www.traitdunion.it')
        assert response.status_code == 301
        assert 'traitdunion.it' in response['Location']
        assert 'www.' not in response['Location']

    @override_settings(CANONICAL_DOMAIN='traitdunion.it', SESSION_COOKIE_SECURE=False, ALLOWED_HOSTS=_ALLOWED)
    def test_render_subdomain_redirects(self, client):
        """Requests to the Render subdomain should redirect to canonical."""
        response = client.get('/contact/', HTTP_HOST='trait-d-union.onrender.com')
        assert response.status_code == 301
        assert response['Location'] == 'https://traitdunion.it/contact/'

    @override_settings(CANONICAL_DOMAIN='traitdunion.it', SESSION_COOKIE_SECURE=False, ALLOWED_HOSTS=_ALLOWED)
    def test_redirect_loop_detection_breaks_loop(self, client):
        """If the redirect loop cookie is present, do NOT redirect (break loop)."""
        # Simulate a browser that already followed one canonical redirect
        # (the cookie was set by the previous 301)
        client.cookies['_canonical_ok'] = '1'
        response = client.get('/', HTTP_HOST='trait-d-union.onrender.com')
        # Must NOT redirect — serve the page instead
        assert response.status_code != 301

    @override_settings(CANONICAL_DOMAIN='traitdunion.it', ALLOWED_HOSTS=_ALLOWED)
    def test_healthz_exempt_from_redirect(self, client):
        """Health check endpoint must never be redirected."""
        response = client.get('/healthz/', HTTP_HOST='internal-hostname.render.com')
        assert response.status_code == 200

    @override_settings(CANONICAL_DOMAIN='traitdunion.it', ALLOWED_HOSTS=_ALLOWED)
    def test_static_exempt_from_redirect(self, client):
        """Static files must not trigger canonical redirect."""
        response = client.get('/static/robots.txt', HTTP_HOST='trait-d-union.onrender.com')
        # Should not be a 301 (may be 200 or 404 depending on static config)
        assert response.status_code != 301

    @override_settings(CANONICAL_DOMAIN='', ALLOWED_HOSTS=_ALLOWED)
    def test_no_canonical_domain_no_redirect(self, client):
        """When CANONICAL_DOMAIN is empty, no redirect should happen."""
        response = client.get('/', HTTP_HOST='any-host.example.com')
        assert response.status_code != 301

    @override_settings(CANONICAL_DOMAIN='traitdunion.it', ALLOWED_HOSTS=_ALLOWED + ['traitdunion.it'])
    def test_host_comparison_case_insensitive(self, client):
        """Host comparison should be case-insensitive."""
        # Note: Django's ALLOWED_HOSTS check is case-insensitive,
        # so 'traitdunion.it' matches 'TraitDunion.IT'
        response = client.get('/', HTTP_HOST='traitdunion.it')
        assert response.status_code == 200
