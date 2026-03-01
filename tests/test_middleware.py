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
