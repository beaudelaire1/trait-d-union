"""Tests for core services: captcha, email_obfuscator, utils, context_processors, forms."""
import base64
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
import requests
from django.test import RequestFactory, override_settings

from core.services.email_obfuscator import obfuscate_email, get_company_email_obfuscated
from core.services.captcha import verify_recaptcha, verify_turnstile, _has_keys
from core.utils import num2words_fr
from core.context_processors import captcha_settings, breadcrumbs


# ==============================================================================
# EMAIL OBFUSCATOR
# ==============================================================================

class TestObfuscateEmail:
    def test_obfuscate_encodes_base64(self):
        result = obfuscate_email('test@example.com')
        decoded = base64.b64decode(result['encoded']).decode('utf-8')
        assert decoded == 'test@example.com'

    def test_obfuscate_display_replaces_at_and_dot(self):
        result = obfuscate_email('test@example.com')
        assert result['display'] == 'test [at] example [dot] com'

    def test_obfuscate_no_original_field(self):
        """🛡️ SECURITY: original email must NOT be exposed in the returned dict."""
        result = obfuscate_email('test@example.com')
        assert 'original' not in result

    def test_company_email(self):
        result = get_company_email_obfuscated()
        assert 'original' not in result
        assert '[at]' in result['display']


# ==============================================================================
# CAPTCHA
# ==============================================================================

class TestHasKeys:
    def test_both_keys_present(self):
        assert _has_keys('site', 'secret') is True

    def test_missing_site_key(self):
        assert _has_keys('', 'secret') is False

    def test_missing_secret_key(self):
        assert _has_keys('site', '') is False

    def test_both_empty(self):
        assert _has_keys('', '') is False


class TestRecaptcha:
    @override_settings(RECAPTCHA_SECRET_KEY='', RECAPTCHA_SITE_KEY='')
    def test_no_keys_passes(self):
        assert verify_recaptcha('any-token') is True

    @override_settings(RECAPTCHA_SECRET_KEY='secret', RECAPTCHA_SITE_KEY='site')
    def test_empty_token_fails(self):
        assert verify_recaptcha('') is False

    @override_settings(RECAPTCHA_SECRET_KEY='secret', RECAPTCHA_SITE_KEY='site')
    @patch('core.services.captcha.requests.post')
    def test_valid_token_passes(self, mock_post):
        mock_post.return_value.json.return_value = {'success': True}
        assert verify_recaptcha('valid-token', '1.2.3.4') is True

    @override_settings(RECAPTCHA_SECRET_KEY='secret', RECAPTCHA_SITE_KEY='site')
    @patch('core.services.captcha.requests.post')
    def test_invalid_token_fails(self, mock_post):
        mock_post.return_value.json.return_value = {'success': False, 'error-codes': ['invalid-input-response']}
        assert verify_recaptcha('bad-token') is False

    @override_settings(RECAPTCHA_SECRET_KEY='secret', RECAPTCHA_SITE_KEY='site')
    @patch('core.services.captcha.requests.post')
    def test_invalid_secret_fails_closed(self, mock_post):
        mock_post.return_value.json.return_value = {'success': False, 'error-codes': ['invalid-input-secret']}
        assert verify_recaptcha('token') is False

    @override_settings(RECAPTCHA_SECRET_KEY='secret', RECAPTCHA_SITE_KEY='site')
    @patch('core.services.captcha.requests.post')
    def test_network_error_fails_closed(self, mock_post):
        mock_post.side_effect = requests.RequestException("timeout")
        assert verify_recaptcha('token') is False

    @override_settings(RECAPTCHA_SECRET_KEY='secret', RECAPTCHA_SITE_KEY='site')
    @patch('core.services.captcha.requests.post')
    def test_timeout_fails_closed(self, mock_post):
        mock_post.side_effect = requests.Timeout("timeout")
        assert verify_recaptcha('token') is False


class TestTurnstile:
    @override_settings(TURNSTILE_SECRET_KEY='', TURNSTILE_SITE_KEY='')
    def test_no_keys_passes(self):
        assert verify_turnstile('any-token') is True

    @override_settings(TURNSTILE_SECRET_KEY='secret', TURNSTILE_SITE_KEY='site')
    def test_empty_token_fails(self):
        assert verify_turnstile('') is False

    @override_settings(TURNSTILE_SECRET_KEY='secret', TURNSTILE_SITE_KEY='site')
    @patch('core.services.captcha.requests.post')
    def test_valid_token_passes(self, mock_post):
        mock_post.return_value.json.return_value = {'success': True}
        assert verify_turnstile('valid-token', '1.2.3.4') is True

    @override_settings(TURNSTILE_SECRET_KEY='secret', TURNSTILE_SITE_KEY='site')
    @patch('core.services.captcha.requests.post')
    def test_invalid_token_fails(self, mock_post):
        mock_post.return_value.json.return_value = {'success': False, 'error-codes': ['invalid-input-response']}
        assert verify_turnstile('bad-token') is False

    @override_settings(TURNSTILE_SECRET_KEY='secret', TURNSTILE_SITE_KEY='site')
    @patch('core.services.captcha.requests.post')
    def test_network_error_fails_closed(self, mock_post):
        mock_post.side_effect = requests.RequestException("timeout")
        assert verify_turnstile('token') is False


# ==============================================================================
# UTILS
# ==============================================================================

class TestNum2WordsFr:
    def test_with_value(self):
        result = num2words_fr(Decimal('42'))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_decimal_value(self):
        result = num2words_fr(Decimal('123.45'))
        assert isinstance(result, str)


# ==============================================================================
# CONTEXT PROCESSORS
# ==============================================================================

class TestCaptchaSettings:
    def test_returns_keys(self):
        factory = RequestFactory()
        request = factory.get('/')
        result = captcha_settings(request)
        assert 'turnstile_site_key' in result
        assert 'recaptcha_site_key' in result
        assert 'ga4_measurement_id' in result
        assert 'turnstile_fallback_timeout_ms' in result

    @override_settings(TURNSTILE_FALLBACK_TIMEOUT_MS='invalid')
    def test_invalid_timeout_defaults_to_2500(self):
        factory = RequestFactory()
        request = factory.get('/')
        result = captcha_settings(request)
        assert result['turnstile_fallback_timeout_ms'] == 2500


class TestBreadcrumbs:
    def test_root_path(self):
        factory = RequestFactory()
        request = factory.get('/')
        result = breadcrumbs(request)
        assert result['breadcrumbs_list'][0]['name'] == 'Accueil'

    def test_services_path(self):
        factory = RequestFactory()
        request = factory.get('/services/')
        result = breadcrumbs(request)
        names = [b['name'] for b in result['breadcrumbs_list']]
        assert 'Accueil' in names
        assert 'Nos Services' in names

    def test_nested_path(self):
        factory = RequestFactory()
        request = factory.get('/portfolio/mon-projet/')
        result = breadcrumbs(request)
        names = [b['name'] for b in result['breadcrumbs_list']]
        assert 'Accueil' in names
        assert 'Portfolio' in names

    def test_numeric_segment_skipped(self):
        factory = RequestFactory()
        request = factory.get('/chroniques/123/')
        result = breadcrumbs(request)
        names = [b['name'] for b in result['breadcrumbs_list']]
        assert '123' not in names

    def test_unknown_segment_title_cased(self):
        factory = RequestFactory()
        request = factory.get('/custom-page/')
        result = breadcrumbs(request)
        names = [b['name'] for b in result['breadcrumbs_list']]
        assert 'Custom Page' in names


# ==============================================================================
# CORE FORMS
# ==============================================================================

class TestCaptchaLoginFormHelpers:
    def test_get_client_ip_with_forwarded_for(self):
        from core.forms import _get_client_ip
        factory = RequestFactory()
        request = factory.get('/', HTTP_X_FORWARDED_FOR='1.2.3.4, 10.0.0.1')
        assert _get_client_ip(request) == '1.2.3.4'

    def test_get_client_ip_without_forwarded_for(self):
        from core.forms import _get_client_ip
        factory = RequestFactory()
        request = factory.get('/')
        ip = _get_client_ip(request)
        assert isinstance(ip, str)

    def test_get_client_ip_none_request(self):
        from core.forms import _get_client_ip
        assert _get_client_ip(None) == ''

    @override_settings(TURNSTILE_SITE_KEY='', TURNSTILE_SECRET_KEY='')
    def test_has_turnstile_false_no_keys(self):
        from core.forms import _has_turnstile
        assert _has_turnstile() is False

    @override_settings(RECAPTCHA_SITE_KEY='', RECAPTCHA_SECRET_KEY='')
    def test_has_recaptcha_false_no_keys(self):
        from core.forms import _has_recaptcha
        assert _has_recaptcha() is False

    @override_settings(TURNSTILE_SITE_KEY='sk', TURNSTILE_SECRET_KEY='secret')
    def test_has_turnstile_true_with_keys(self):
        from core.forms import _has_turnstile
        assert _has_turnstile() is True

    @override_settings(RECAPTCHA_SITE_KEY='sk', RECAPTCHA_SECRET_KEY='secret')
    def test_has_recaptcha_true_with_keys(self):
        from core.forms import _has_recaptcha
        assert _has_recaptcha() is True
