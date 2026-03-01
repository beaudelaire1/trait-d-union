"""Tests for core/services: brevo_backend, email_backends, crm_service, stripe_service,
signature_service, image_processor, payment_email_service."""
import base64
import io
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.test import override_settings


# ==============================================================================
# BREVO EMAIL BACKEND
# ==============================================================================

class TestBrevoEmailBackend:

    @override_settings(BREVO_API_KEY='')
    def test_send_messages_no_api_key_returns_zero(self):
        from core.services.brevo_backend import BrevoEmailBackend
        backend = BrevoEmailBackend()
        msg = EmailMessage(subject='Test', body='Body', to=['test@example.com'])
        assert backend.send_messages([msg]) == 0

    @override_settings(BREVO_API_KEY='test-key')
    @patch('core.services.brevo_backend.BrevoEmailBackend._send_one', return_value=True)
    def test_send_messages_success(self, mock_send):
        from core.services.brevo_backend import BrevoEmailBackend
        backend = BrevoEmailBackend()
        msg = EmailMessage(subject='Test', body='Body', to=['test@example.com'])
        assert backend.send_messages([msg]) == 1

    @override_settings(BREVO_API_KEY='test-key')
    @patch('core.services.brevo_backend.BrevoEmailBackend._send_one', side_effect=Exception('API'))
    def test_send_messages_error_silent(self, mock_send):
        from core.services.brevo_backend import BrevoEmailBackend
        backend = BrevoEmailBackend(fail_silently=True)
        msg = EmailMessage(subject='Test', body='Body', to=['test@example.com'])
        assert backend.send_messages([msg]) == 0

    @override_settings(BREVO_API_KEY='test-key')
    @patch('core.services.brevo_backend.BrevoEmailBackend._send_one', side_effect=Exception('API'))
    def test_send_messages_error_raises(self, mock_send):
        from core.services.brevo_backend import BrevoEmailBackend
        backend = BrevoEmailBackend(fail_silently=False)
        msg = EmailMessage(subject='Test', body='Body', to=['test@example.com'])
        with pytest.raises(Exception, match='API'):
            backend.send_messages([msg])

    @override_settings(BREVO_API_KEY='test-key')
    def test_send_one_with_html_alternative(self):
        from core.services.brevo_backend import BrevoEmailBackend
        backend = BrevoEmailBackend()
        mock_api = MagicMock()
        mock_api.send_transac_email.return_value = MagicMock(message_id='abc123')
        backend._api_instance = mock_api

        msg = EmailMultiAlternatives(
            subject='Test', body='Text', to=['to@example.com'], from_email='from@example.com'
        )
        msg.attach_alternative('<p>HTML</p>', 'text/html')

        with patch('core.services.brevo_backend.sib_api_v3_sdk', create=True) as mock_sdk:
            mock_sdk.SendSmtpEmail.return_value = MagicMock()
            mock_sdk.SendSmtpEmailTo.return_value = MagicMock()
            mock_sdk.SendSmtpEmailSender.return_value = MagicMock()
            result = backend._send_one(msg)
            assert result is True

    @override_settings(BREVO_API_KEY='test-key')
    def test_send_one_with_bcc_cc_reply(self):
        from core.services.brevo_backend import BrevoEmailBackend
        backend = BrevoEmailBackend()
        mock_api = MagicMock()
        mock_api.send_transac_email.return_value = MagicMock(message_id='abc')
        backend._api_instance = mock_api

        msg = EmailMessage(
            subject='Test', body='Body', to=['to@e.com'],
            cc=['cc@e.com'], bcc=['bcc@e.com'], reply_to=['reply@e.com'],
            from_email='from@e.com',
        )

        with patch('core.services.brevo_backend.sib_api_v3_sdk', create=True) as mock_sdk:
            mock_sdk.SendSmtpEmail.return_value = MagicMock()
            mock_sdk.SendSmtpEmailTo.return_value = MagicMock()
            mock_sdk.SendSmtpEmailSender.return_value = MagicMock()
            mock_sdk.SendSmtpEmailBcc.return_value = MagicMock()
            mock_sdk.SendSmtpEmailCc.return_value = MagicMock()
            mock_sdk.SendSmtpEmailReplyTo.return_value = MagicMock()
            assert backend._send_one(msg) is True

    @override_settings(BREVO_API_KEY='test-key')
    def test_send_one_with_attachments(self):
        from core.services.brevo_backend import BrevoEmailBackend
        backend = BrevoEmailBackend()
        mock_api = MagicMock()
        mock_api.send_transac_email.return_value = MagicMock(message_id='abc')
        backend._api_instance = mock_api

        msg = EmailMessage(subject='Test', body='Body', to=['to@e.com'], from_email='f@e.com')
        msg.attach('file.pdf', b'%PDF', 'application/pdf')

        with patch('core.services.brevo_backend.sib_api_v3_sdk', create=True) as mock_sdk:
            mock_sdk.SendSmtpEmail.return_value = MagicMock()
            mock_sdk.SendSmtpEmailTo.return_value = MagicMock()
            mock_sdk.SendSmtpEmailSender.return_value = MagicMock()
            mock_sdk.SendSmtpEmailAttachment.return_value = MagicMock()
            assert backend._send_one(msg) is True

    @override_settings(BREVO_API_KEY='test-key')
    def test_send_one_html_content_subtype(self):
        from core.services.brevo_backend import BrevoEmailBackend
        backend = BrevoEmailBackend()
        mock_api = MagicMock()
        mock_api.send_transac_email.return_value = MagicMock(message_id='abc')
        backend._api_instance = mock_api

        msg = EmailMessage(subject='Test', body='<h1>HTML</h1>', to=['to@e.com'], from_email='f@e.com')
        msg.content_subtype = 'html'

        with patch('core.services.brevo_backend.sib_api_v3_sdk', create=True) as mock_sdk:
            mock_sdk.SendSmtpEmail.return_value = MagicMock()
            mock_sdk.SendSmtpEmailTo.return_value = MagicMock()
            mock_sdk.SendSmtpEmailSender.return_value = MagicMock()
            assert backend._send_one(msg) is True


# ==============================================================================
# BREVO EMAIL SERVICE (email_backends.py)
# ==============================================================================

class TestBrevoEmailService:
    @override_settings(BREVO_API_KEY=None)
    def test_not_configured(self):
        from core.services.email_backends import BrevoEmailService
        service = BrevoEmailService()
        assert service.is_configured() is False

    @override_settings(BREVO_API_KEY='test-key')
    def test_is_configured(self):
        from core.services.email_backends import BrevoEmailService
        service = BrevoEmailService()
        assert service.is_configured() is True

    @override_settings(BREVO_API_KEY=None)
    def test_send_email_not_configured(self):
        from core.services.email_backends import BrevoEmailService
        service = BrevoEmailService()
        result = service.send_email('to@ex.com', 'Subject', '<p>HTML</p>')
        assert result['success'] is False

    @override_settings(BREVO_API_KEY=None, DEFAULT_FROM_EMAIL='test@tus.it')
    def test_send_simple_email_fallback_django(self):
        from core.services.email_backends import send_simple_email
        result = send_simple_email(
            to_email='to@ex.com', subject='Subj', text_body='Hello',
            from_email='test@tus.it',
        )
        # send_simple_email returns True/False, not a dict
        assert result is True


# ==============================================================================
# CRM SERVICE
# ==============================================================================

class TestAirtableService:
    @patch.dict('os.environ', {'AIRTABLE_API_KEY': '', 'AIRTABLE_BASE_ID': ''}, clear=False)
    def test_not_configured_by_default(self):
        from core.services.crm_service import AirtableService
        service = AirtableService()
        assert service.is_configured is False  # Property, not method

    @patch.dict('os.environ', {'AIRTABLE_API_KEY': 'patXXX', 'AIRTABLE_BASE_ID': 'appXXX', 'AIRTABLE_TABLE_NAME': 'Leads'})
    def test_configured_with_env(self):
        from core.services.crm_service import AirtableService
        service = AirtableService()
        assert service.is_configured is True

    @patch.dict('os.environ', {'AIRTABLE_API_KEY': 'patXXX', 'AIRTABLE_BASE_ID': 'appXXX', 'AIRTABLE_TABLE_NAME': 'Leads'})
    @patch('core.services.crm_service.requests.post')
    def test_create_lead_success(self, mock_post):
        from core.services.crm_service import AirtableService
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'id': 'recXXX'}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp
        service = AirtableService()
        result = service.create_lead({'name': 'Test', 'email': 'test@ex.com'})
        assert result == 'recXXX'

    @patch.dict('os.environ', {'AIRTABLE_API_KEY': '', 'AIRTABLE_BASE_ID': ''}, clear=False)
    def test_create_lead_not_configured(self):
        from core.services.crm_service import AirtableService
        service = AirtableService()
        result = service.create_lead({'name': 'Test'})
        assert result is None

    @patch.dict('os.environ', {'AIRTABLE_API_KEY': 'patXXX', 'AIRTABLE_BASE_ID': 'appXXX', 'AIRTABLE_TABLE_NAME': 'Leads'})
    @patch('core.services.crm_service.requests.patch')
    def test_update_lead(self, mock_patch):
        from core.services.crm_service import AirtableService
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_patch.return_value = mock_resp
        service = AirtableService()
        result = service.update_lead('recXXX', {'Status': 'Qualified'})
        assert result is True

    @patch.dict('os.environ', {'AIRTABLE_API_KEY': 'patXXX', 'AIRTABLE_BASE_ID': 'appXXX'})
    def test_headers(self):
        from core.services.crm_service import AirtableService
        service = AirtableService()
        headers = service._headers()
        assert 'Authorization' in headers
        assert 'Bearer' in headers['Authorization']

    @patch.dict('os.environ', {'AIRTABLE_API_KEY': 'patXXX', 'AIRTABLE_BASE_ID': 'appXXX', 'AIRTABLE_TABLE_NAME': 'Leads'})
    def test_endpoint(self):
        from core.services.crm_service import AirtableService
        service = AirtableService()
        assert 'appXXX' in service._endpoint()
        assert 'Leads' in service._endpoint()


class TestHubSpotService:
    @patch.dict('os.environ', {'HUBSPOT_API_KEY': ''}, clear=False)
    def test_not_configured_by_default(self):
        from core.services.crm_service import HubSpotService
        service = HubSpotService()
        assert service.is_configured is False

    @patch.dict('os.environ', {'HUBSPOT_API_KEY': 'pat-xxx'})
    def test_configured_with_env(self):
        from core.services.crm_service import HubSpotService
        service = HubSpotService()
        assert service.is_configured is True

    @patch.dict('os.environ', {'HUBSPOT_API_KEY': 'pat-xxx'})
    @patch('core.services.crm_service.requests.post')
    def test_create_contact_success(self, mock_post):
        from core.services.crm_service import HubSpotService
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {'id': '123'}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp
        service = HubSpotService()
        result = service.create_contact({'email': 'test@ex.com', 'first_name': 'Test'})
        assert result == '123'

    @patch.dict('os.environ', {'HUBSPOT_API_KEY': ''}, clear=False)
    def test_create_contact_not_configured(self):
        from core.services.crm_service import HubSpotService
        service = HubSpotService()
        result = service.create_contact({'email': 'test@ex.com'})
        assert result is None

    @patch.dict('os.environ', {'HUBSPOT_API_KEY': ''}, clear=False)
    def test_create_deal_not_configured(self):
        from core.services.crm_service import HubSpotService
        service = HubSpotService()
        result = service.create_deal({'name': 'Deal'})
        assert result is None

    @patch.dict('os.environ', {'HUBSPOT_API_KEY': 'pat-xxx'})
    @patch('core.services.crm_service.requests.post')
    def test_create_deal_success(self, mock_post):
        from core.services.crm_service import HubSpotService
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {'id': '456'}
        mock_post.return_value = mock_resp
        service = HubSpotService()
        result = service.create_deal({'name': 'Deal', 'amount': '5000'}, contact_id='123')
        assert result == '456'

    @patch.dict('os.environ', {'HUBSPOT_API_KEY': 'pat-xxx'})
    @patch('core.services.crm_service.requests.get')
    def test_find_contact_by_email(self, mock_get):
        from core.services.crm_service import HubSpotService
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {'id': '789'}
        mock_get.return_value = mock_resp
        service = HubSpotService()
        result = service._find_contact_by_email('test@ex.com')
        assert result == '789'

    @patch.dict('os.environ', {'HUBSPOT_API_KEY': 'pat-xxx'})
    def test_find_contact_empty_email(self):
        from core.services.crm_service import HubSpotService
        service = HubSpotService()
        assert service._find_contact_by_email('') is None


class TestCRMService:
    @patch.dict('os.environ', {'AIRTABLE_API_KEY': '', 'AIRTABLE_BASE_ID': '', 'HUBSPOT_API_KEY': ''}, clear=False)
    def test_not_configured_by_default(self):
        from core.services.crm_service import CRMService
        service = CRMService()
        assert service.is_configured is False

    @patch.dict('os.environ', {'AIRTABLE_API_KEY': '', 'AIRTABLE_BASE_ID': '', 'HUBSPOT_API_KEY': ''}, clear=False)
    def test_sync_lead_not_configured(self):
        from core.services.crm_service import CRMService
        service = CRMService()
        mock_lead = MagicMock()
        mock_lead.name = 'Test Lead'
        mock_lead.email = 'test@ex.com'
        mock_lead.phone = ''
        mock_lead.message = 'Hello'
        mock_lead.company = ''
        result = service.sync_lead(mock_lead)
        assert result['airtable_id'] is None
        assert result['hubspot_id'] is None


# ==============================================================================
# STRIPE SERVICE
# ==============================================================================

class TestStripeService:
    @patch.dict('os.environ', {'STRIPE_SECRET_KEY': '', 'STRIPE_PUBLISHABLE_KEY': ''}, clear=False)
    def test_not_configured(self):
        from core.services.stripe_service import is_stripe_configured
        assert is_stripe_configured() is False

    @patch.dict('os.environ', {'STRIPE_SECRET_KEY': 'sk_test_fake', 'STRIPE_PUBLISHABLE_KEY': 'pk_test_fake'})
    def test_configured(self):
        from core.services.stripe_service import is_stripe_configured, STRIPE_AVAILABLE
        if STRIPE_AVAILABLE:
            assert is_stripe_configured() is True
        else:
            assert is_stripe_configured() is False  # stripe package not installed

    @patch.dict('os.environ', {'STRIPE_SECRET_KEY': 'sk_test', 'STRIPE_PUBLISHABLE_KEY': 'pk_test', 'STRIPE_WEBHOOK_SECRET': 'whsec'})
    def test_get_stripe_keys(self):
        from core.services.stripe_service import get_stripe_keys
        keys = get_stripe_keys()
        assert keys['secret_key'] == 'sk_test'
        assert keys['publishable_key'] == 'pk_test'
        assert keys['webhook_secret'] == 'whsec'

    def test_handle_checkout_completed_unknown_type(self):
        from core.services.stripe_service import StripePaymentService
        session = {'metadata': {'payment_type': 'unknown'}}
        result = StripePaymentService.handle_checkout_completed(session)
        assert result is False

    def test_handle_checkout_completed_no_metadata(self):
        from core.services.stripe_service import StripePaymentService
        session = {'metadata': {}}
        result = StripePaymentService.handle_checkout_completed(session)
        assert result is False

    def test_default_deposit_rate(self):
        from core.services.stripe_service import StripePaymentService
        assert StripePaymentService.DEFAULT_DEPOSIT_RATE == Decimal('0.30')


# ==============================================================================
# SIGNATURE SERVICE
# ==============================================================================

class TestSignatureService:
    def test_validate_empty_data(self):
        from core.services.signature_service import SignatureService
        valid, msg = SignatureService.validate_signature_data('')
        assert valid is False
        assert 'Aucune' in msg

    def test_validate_too_large_data(self):
        from core.services.signature_service import SignatureService
        large_data = 'A' * (600 * 1024)
        valid, msg = SignatureService.validate_signature_data(large_data)
        assert valid is False
        assert 'volumineuse' in msg

    def test_validate_invalid_base64(self):
        from core.services.signature_service import SignatureService
        valid, msg = SignatureService.validate_signature_data('not-valid-base64!!!')
        assert valid is False

    def test_validate_with_data_prefix(self):
        from core.services.signature_service import SignatureService
        # Create a minimal valid PNG as base64
        from PIL import Image
        img = Image.new('RGBA', (200, 100), (0, 0, 0, 255))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        b64 = base64.b64encode(buf.getvalue()).decode()
        data = f'data:image/png;base64,{b64}'
        valid, msg = SignatureService.validate_signature_data(data)
        assert valid is True

    def test_compute_signature_hash(self):
        from core.services.signature_service import SignatureService
        data = base64.b64encode(b'test-image-data').decode()
        result = SignatureService.compute_signature_hash(data)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex

    def test_compute_hash_with_prefix(self):
        from core.services.signature_service import SignatureService
        data = 'data:image/png;base64,' + base64.b64encode(b'test').decode()
        result = SignatureService.compute_signature_hash(data)
        assert len(result) == 64

    def test_generate_audit_trail(self):
        from core.services.signature_service import SignatureService
        trail = SignatureService.generate_audit_trail(
            client_ip='1.2.3.4',
            user_agent='Mozilla/5.0',
            document_type='quote',
            document_id='123',
            document_number='DEV-2026-001',
            signer_name='Jean Dupont',
            signer_email='jean@example.com',
        )
        assert trail['technical']['ip_address'] == '1.2.3.4'
        assert trail['document']['type'] == 'quote'
        assert trail['signer']['name'] == 'Jean Dupont'
        assert 'integrity_hash' in trail
        assert len(trail['integrity_hash']) == 64

    def test_get_client_ip_with_forwarded(self):
        from core.services.signature_service import SignatureService
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/', HTTP_X_FORWARDED_FOR='1.2.3.4, 10.0.0.1')
        ip = SignatureService.get_client_ip(request)
        assert ip == '1.2.3.4'

    def test_get_client_ip_without_forwarded(self):
        from core.services.signature_service import SignatureService
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        ip = SignatureService.get_client_ip(request)
        assert isinstance(ip, str)

    @override_settings(MEDIA_ROOT='/tmp/test_media')
    def test_save_signature_image(self):
        from core.services.signature_service import SignatureService
        b64 = base64.b64encode(b'fake-png-data').decode()
        path = SignatureService.save_signature_image(b64, 'test_sig')
        assert path is not None
        assert 'test_sig.png' in path

    def test_save_signature_invalid_base64(self):
        from core.services.signature_service import SignatureService
        # Invalid base64 with characters that fail validate=True
        result = SignatureService.save_signature_image('not!valid!base64!!!', 'test')
        assert result is None


# ==============================================================================
# IMAGE PROCESSOR
# ==============================================================================

class TestImageProcessor:
    def test_is_supported_jpg(self):
        from core.services.image_processor import ImageProcessor
        processor = ImageProcessor()
        assert processor.is_supported('photo.jpg') is True

    def test_is_supported_png(self):
        from core.services.image_processor import ImageProcessor
        processor = ImageProcessor()
        assert processor.is_supported('photo.png') is True

    def test_is_not_supported_webp(self):
        from core.services.image_processor import ImageProcessor
        processor = ImageProcessor()
        assert processor.is_supported('photo.webp') is False

    def test_is_not_supported_txt(self):
        from core.services.image_processor import ImageProcessor
        processor = ImageProcessor()
        assert processor.is_supported('doc.txt') is False

    def test_pillow_available_is_bool(self):
        from core.services.image_processor import ImageProcessor
        processor = ImageProcessor()
        assert isinstance(processor.pillow_available, bool)

    def test_convert_to_webp(self):
        from core.services.image_processor import ImageProcessor
        from PIL import Image
        processor = ImageProcessor()
        img = Image.new('RGB', (200, 200), (255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        buf.name = 'test.png'
        result = processor.convert_to_webp(buf)
        if processor._webp_support:
            assert result is not None
            assert result.name.endswith('.webp')

    def test_create_thumbnail(self):
        from core.services.image_processor import ImageProcessor
        from PIL import Image
        processor = ImageProcessor()
        img = Image.new('RGB', (800, 600), (0, 255, 0))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        buf.name = 'test.png'
        result = processor.create_thumbnail(buf, size=(200, 150))
        assert result is not None

    def test_optimize_for_web(self):
        from core.services.image_processor import ImageProcessor
        from PIL import Image
        processor = ImageProcessor()
        img = Image.new('RGB', (400, 300), (0, 0, 255))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        buf.name = 'test.png'
        result = processor.optimize_for_web(buf)
        assert 'original' in result
        assert 'webp' in result

    def test_init_custom_quality(self):
        from core.services.image_processor import ImageProcessor
        processor = ImageProcessor(quality_webp=70, quality_avif=60)
        assert processor.quality_webp == 70
        assert processor.quality_avif == 60


# ==============================================================================
# DOCUMENT GENERATOR
# ==============================================================================

class TestDocumentGenerator:
    def test_get_branding(self):
        from core.services.document_generator import DocumentGenerator
        branding = DocumentGenerator.get_branding()
        assert isinstance(branding, dict)
        assert 'name' in branding

    def test_patch_fonts_strips_google_fonts(self):
        from core.services.document_generator import DocumentGenerator
        # Use the exact google fonts import string from the source code
        html = """<style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');</style>"""
        patched = DocumentGenerator._patch_fonts(html)
        assert 'fonts.googleapis.com' not in patched
        assert 'font-face' in patched

    def test_patch_fonts_no_change_if_no_import(self):
        from core.services.document_generator import DocumentGenerator
        html = '<style>body { color: red; }</style>'
        patched = DocumentGenerator._patch_fonts(html)
        assert patched == html
