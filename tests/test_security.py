"""Tests for security configuration.

Verifies that security headers, authentication settings, and access controls
are correctly configured at the Django settings level.
"""
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


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

    def test_session_inactivity_timeout(self):
        """Session must expire after 15 minutes of inactivity (900s)."""
        assert settings.SESSION_COOKIE_AGE == 900
        assert settings.SESSION_SAVE_EVERY_REQUEST is True
        assert settings.SESSION_EXPIRE_AT_BROWSER_CLOSE is False

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


@pytest.mark.django_db
class TestSessionPing:
    """Tests for the session keep-alive endpoint."""

    def test_anonymous_gets_403(self, client):
        """Anonymous users must not be able to ping."""
        response = client.get('/tus-gestion-secure/session-ping/')
        assert response.status_code == 403

    def test_non_staff_gets_403(self, client):
        """Non-staff authenticated users must not be able to ping."""
        user = User.objects.create_user(
            username='regular', password='testpass123', email='r@test.com',
        )
        client.force_login(user)
        response = client.get('/tus-gestion-secure/session-ping/')
        assert response.status_code == 403

    def test_staff_gets_204(self, client):
        """Staff users get 204 No Content (session renewed)."""
        user = User.objects.create_user(
            username='staffuser', password='testpass123',
            email='s@test.com', is_staff=True,
        )
        client.force_login(user)
        response = client.get('/tus-gestion-secure/session-ping/')
        assert response.status_code == 204

    def test_post_not_allowed(self, client):
        """Only GET is accepted."""
        user = User.objects.create_user(
            username='staffpost', password='testpass123',
            email='sp@test.com', is_staff=True,
        )
        client.force_login(user)
        response = client.post('/tus-gestion-secure/session-ping/')
        assert response.status_code == 405

    def test_ping_updates_last_activity(self, client):
        """Ping should store _last_activity in the session."""
        user = User.objects.create_user(
            username='staffact', password='testpass123',
            email='sa@test.com', is_staff=True,
        )
        client.force_login(user)
        response = client.get('/tus-gestion-secure/session-ping/')
        assert response.status_code == 204
        assert '_last_activity' in client.session

    def test_no_cache_header(self, client):
        """Ping response must not be cached."""
        user = User.objects.create_user(
            username='staffcache', password='testpass123',
            email='sc@test.com', is_staff=True,
        )
        client.force_login(user)
        response = client.get('/tus-gestion-secure/session-ping/')
        assert 'no-store' in response.get('Cache-Control', '')
