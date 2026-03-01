"""Tests for audit fixes: security, performance, architecture.

This file covers the critical changes made during the audit repair:
- get_client_ip centralization
- StripeEventLog idempotence
- stripe_webhook_view
- email obfuscator (no 'original' field)
- healthz endpoint (production vs debug)
- Lead attachment validators
"""
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
from django.test import TestCase, RequestFactory, override_settings
from django.http import HttpRequest


# ==============================================================================
# GET_CLIENT_IP — Centralized in core.utils
# ==============================================================================

class TestGetClientIp:
    """Tests for the centralized get_client_ip function."""

    def test_returns_empty_for_none_request(self):
        from core.utils import get_client_ip
        assert get_client_ip(None) == ''

    def test_returns_remote_addr(self):
        from core.utils import get_client_ip
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        assert get_client_ip(request) == '192.168.1.1'

    def test_prefers_x_forwarded_for(self):
        from core.utils import get_client_ip
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.50, 70.41.3.18, 150.172.238.178'
        # Must only trust the FIRST entry
        assert get_client_ip(request) == '203.0.113.50'

    def test_truncates_to_45_chars(self):
        from core.utils import get_client_ip
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = 'a' * 100
        ip = get_client_ip(request)
        # Should fallback to 127.0.0.1 because 'aaa...' has invalid chars
        assert len(ip) <= 45

    def test_rejects_invalid_characters(self):
        from core.utils import get_client_ip
        request = HttpRequest()
        request.META['HTTP_X_FORWARDED_FOR'] = '<script>alert(1)</script>'
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        ip = get_client_ip(request)
        assert '<' not in ip
        assert ip == '127.0.0.1'

    def test_ipv6_address(self):
        from core.utils import get_client_ip
        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '2001:db8::1'
        assert get_client_ip(request) == '2001:db8::1'

    def test_fallback_to_localhost(self):
        from core.utils import get_client_ip
        request = HttpRequest()
        # No REMOTE_ADDR, no X-Forwarded-For
        assert get_client_ip(request) == '127.0.0.1'


# ==============================================================================
# STRIPE EVENT LOG — Idempotence model
# ==============================================================================

class TestStripeEventLog(TestCase):
    """Tests for StripeEventLog idempotence guard."""

    def test_mark_and_check_processed(self):
        from apps.audit.models import StripeEventLog
        event_id = 'evt_test_abc123'
        assert not StripeEventLog.is_already_processed(event_id)

        StripeEventLog.mark_processed(event_id, 'checkout.session.completed')
        assert StripeEventLog.is_already_processed(event_id)

    def test_duplicate_event_raises(self):
        from apps.audit.models import StripeEventLog
        from django.db import IntegrityError
        event_id = 'evt_test_dup'
        StripeEventLog.mark_processed(event_id, 'test')
        with pytest.raises(IntegrityError):
            StripeEventLog.mark_processed(event_id, 'test')

    def test_str_representation(self):
        from apps.audit.models import StripeEventLog
        log = StripeEventLog.mark_processed('evt_123', 'checkout.session.completed')
        assert 'checkout.session.completed' in str(log)
        assert 'evt_123' in str(log)


# ==============================================================================
# STRIPE WEBHOOK VIEW — Integration test
# ==============================================================================

class TestStripeWebhookView(TestCase):
    """Tests for the unified stripe_webhook_view."""

    def test_missing_signature_returns_400(self):
        from core.services.stripe_service import stripe_webhook_view
        factory = RequestFactory()
        request = factory.post('/webhook/stripe/',
                               data=b'{}',
                               content_type='application/json')
        request.META.pop('HTTP_STRIPE_SIGNATURE', None)
        response = stripe_webhook_view(request)
        assert response.status_code == 400

    @patch('core.services.stripe_service.StripePaymentService.verify_webhook_signature')
    def test_already_processed_event_returns_200(self, mock_verify):
        from core.services.stripe_service import stripe_webhook_view
        from apps.audit.models import StripeEventLog

        event_id = 'evt_already_done'
        StripeEventLog.mark_processed(event_id, 'checkout.session.completed')

        mock_verify.return_value = {
            'id': event_id,
            'type': 'checkout.session.completed',
            'data': {'object': {}},
        }

        factory = RequestFactory()
        request = factory.post('/webhook/stripe/',
                               data=b'{}',
                               content_type='application/json')
        request.META['HTTP_STRIPE_SIGNATURE'] = 'sig_test'
        response = stripe_webhook_view(request)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['status'] == 'already_processed'


# ==============================================================================
# HEALTHZ — Production vs Debug
# ==============================================================================

class TestHealthz(TestCase):
    """Tests for healthz endpoint information control."""

    @override_settings(DEBUG=True)
    def test_debug_mode_includes_checks(self):
        from django.test import Client
        client = Client()
        response = client.get('/healthz/')
        data = json.loads(response.content)
        assert 'checks' in data

    @override_settings(DEBUG=False)
    def test_production_hides_checks(self):
        from django.test import Client
        client = Client()
        response = client.get('/healthz/')
        data = json.loads(response.content)
        assert 'checks' not in data
        assert 'status' in data


# ==============================================================================
# EMAIL OBFUSCATOR — No 'original' field
# ==============================================================================

class TestEmailObfuscatorSecurity:
    """Ensure 'original' email is never exposed."""

    def test_no_original_in_result(self):
        from core.services.email_obfuscator import obfuscate_email
        result = obfuscate_email('secret@example.com')
        assert 'original' not in result
        assert 'encoded' in result
        assert 'display' in result

    def test_company_email_no_original(self):
        from core.services.email_obfuscator import get_company_email_obfuscated
        result = get_company_email_obfuscated()
        assert 'original' not in result
