"""Tests for security configuration.

Verifies that security headers, authentication settings, and access controls
are correctly configured at the Django settings level.
"""
import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse


class TestSecuritySettings:
    """Verify critical security configurations."""

    def test_debug_is_false_in_test(self):
        """DEBUG must be False outside development."""
        assert settings.DEBUG is False

    def test_secret_key_is_set(self):
        """SECRET_KEY must be set."""
        assert settings.SECRET_KEY
        assert len(settings.SECRET_KEY) >= 10

    def test_password_validators_configured(self):
        """At least one password validator must be active."""
        assert len(settings.AUTH_PASSWORD_VALIDATORS) >= 1

    def test_session_cookie_httponly(self):
        """Session cookie must be HttpOnly."""
        assert settings.SESSION_COOKIE_HTTPONLY is True

    def test_x_frame_options(self):
        """X-Frame-Options should be DENY or SAMEORIGIN."""
        assert settings.X_FRAME_OPTIONS in ('DENY', 'SAMEORIGIN')

    def test_logout_requires_post(self):
        """ACCOUNT_LOGOUT_ON_GET must be False to prevent accidental logout."""
        assert settings.ACCOUNT_LOGOUT_ON_GET is False

    def test_email_verification_enabled(self):
        """Email verification must be configured."""
        assert hasattr(settings, 'ACCOUNT_EMAIL_VERIFICATION')
        assert settings.ACCOUNT_EMAIL_VERIFICATION in ('mandatory', 'optional')


@pytest.mark.django_db
class TestAccessControl:
    """Test that protected pages require authentication."""

    def test_admin_requires_login(self, client):
        """Admin panel should redirect unauthenticated users."""
        response = client.get('/tus-gestion-secure/')
        assert response.status_code in (301, 302)

    def test_ecosystem_requires_login(self, client):
        """Écosystème TUS requires authentication."""
        response = client.get('/ecosysteme-tus/')
        assert response.status_code in (301, 302)

    def test_admin_login_page_accessible(self, client):
        """The admin login page itself should be accessible."""
        response = client.get('/tus-gestion-secure/login/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestSecurityHeaders:
    """Test that security headers are present on responses."""

    def test_x_content_type_options(self, client):
        """X-Content-Type-Options: nosniff should be set."""
        response = client.get('/')
        assert response.get('X-Content-Type-Options') == 'nosniff'
