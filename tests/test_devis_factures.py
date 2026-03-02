"""Tests for devis views, factures views, email backends, payment email service."""
import json
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import Client, RequestFactory, override_settings
from django.contrib.auth.models import User

from apps.devis.models import Quote
from apps.factures.models import Invoice
from apps.clients.models import ClientProfile


@pytest.fixture
def staff_user(db):
    return User.objects.create_user('admin_df', 'admin_df@test.com', 'pass123', is_staff=True)


@pytest.fixture
def devis_client(db):
    return ClientProfile.objects.create(
        full_name='Marie Martin', email='marie@test.com', phone='+594600000000',
    )


@pytest.fixture
def quote_fixture(devis_client, db):
    return Quote.objects.create(
        client=devis_client,
        status='draft',
    )


@pytest.fixture
def invoice_fixture(quote_fixture, db):
    return Invoice.objects.create(
        quote=quote_fixture,
    )


# ==============================================================================
# DEVIS PUBLIC VIEWS
# ==============================================================================

@pytest.mark.django_db
class TestPublicDevisView:
    def test_devis_page_loads(self, client):
        response = client.get('/devis/nouveau/')
        assert response.status_code == 200

    def test_devis_page_contains_form(self, client):
        response = client.get('/devis/nouveau/')
        assert b'form' in response.content.lower()

    def test_devis_success_page(self, client):
        response = client.get('/devis/succes/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminDevisViews:
    def test_download_pdf_requires_staff(self, client, quote_fixture):
        response = client.get(f'/devis/telecharger/{quote_fixture.pk}/')
        assert response.status_code == 302

    def test_admin_edit_requires_staff(self, client, quote_fixture):
        response = client.get(f'/devis/admin/{quote_fixture.pk}/')
        assert response.status_code == 302

    def test_admin_generate_pdf_requires_staff(self, client, quote_fixture):
        response = client.post(f'/devis/admin/quote/{quote_fixture.pk}/generate-pdf/')
        assert response.status_code == 302


@pytest.mark.django_db
class TestQuoteValidation:
    def test_validate_start_invalid_token(self, client):
        response = client.get('/devis/valider/nonexistent-token/')
        assert response.status_code == 404

    def test_validate_code_invalid_token(self, client):
        response = client.post('/devis/valider/nonexistent-token/code/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestQuotePublicPdf:
    def test_public_pdf_invalid_token(self, client):
        response = client.get('/devis/pdf/nonexistent-token/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestQuoteSignAndPay:
    def test_sign_and_pay_invalid_token(self, client):
        response = client.get('/devis/valider/nonexistent-token/signer/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestDevisPaymentSuccess:
    def test_payment_success_page(self, client):
        response = client.get('/devis/paiement/succes/')
        assert response.status_code in (200, 302)


@pytest.mark.django_db
class TestStripeWebhook:
    def test_webhook_post_no_signature(self, client):
        response = client.post(
            '/devis/webhook/stripe/',
            data='{}',
            content_type='application/json',
        )
        assert response.status_code in (400, 403, 500)


# ==============================================================================
# FACTURES VIEWS
# ==============================================================================

@pytest.mark.django_db
class TestFacturesViews:
    def test_create_invoice_requires_staff(self, client, quote_fixture):
        response = client.post(f'/factures/create/{quote_fixture.pk}/')
        assert response.status_code == 302

    def test_archive_requires_staff(self, client):
        response = client.get('/factures/archive/')
        assert response.status_code == 302

    def test_archive_loads_for_staff(self, client, staff_user):
        client.force_login(staff_user)
        response = client.get('/factures/archive/')
        assert response.status_code == 200

    def test_download_invoice_requires_staff(self, client, invoice_fixture):
        response = client.get(f'/factures/download/{invoice_fixture.pk}/')
        assert response.status_code == 302


@pytest.mark.django_db
class TestInvoicePayment:
    def test_pay_invalid_token(self, client):
        response = client.get('/factures/payer/nonexistent-token/')
        assert response.status_code == 404

    def test_payment_success_page(self, client):
        response = client.get('/factures/paiement/succes/')
        assert response.status_code in (200, 302)

    def test_payment_cancel_page(self, client):
        response = client.get('/factures/paiement/annule/')
        assert response.status_code == 200

    def test_payment_error_page(self, client):
        response = client.get('/factures/paiement/erreur/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestInvoicePublicPdf:
    def test_public_pdf_invalid_token(self, client):
        response = client.get('/factures/pdf/nonexistent-token/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestInvoiceWebhook:
    def test_webhook_post(self, client):
        response = client.post('/factures/webhook/stripe/', data='{}', content_type='application/json')
        assert response.status_code in (400, 403, 500)


# ==============================================================================
# DEVIS MODELS
# ==============================================================================

@pytest.mark.django_db
class TestDevisModels:
    def test_quote_str(self, quote_fixture):
        s = str(quote_fixture)
        assert isinstance(s, str)
        assert 'DEV' in s or len(s) > 0

    def test_quote_status(self, quote_fixture):
        assert quote_fixture.status == 'draft'

    def test_client_str(self, devis_client):
        assert 'Marie Martin' in str(devis_client)


@pytest.mark.django_db
class TestInvoiceModels:
    def test_invoice_str(self, invoice_fixture):
        s = str(invoice_fixture)
        assert isinstance(s, str)

    def test_invoice_has_number(self, invoice_fixture):
        assert invoice_fixture.number is not None
        assert 'FAC' in invoice_fixture.number


# ==============================================================================
# EMAIL BACKENDS
# ==============================================================================

class TestEmailBackendsFunctions:
    @override_settings(BREVO_API_KEY=None)
    def test_send_transactional_not_configured(self):
        from core.services.email_backends import send_transactional_email
        result = send_transactional_email(
            to_email='test@ex.com', subject='Test', html_content='<p>Hi</p>'
        )
        assert result['success'] is False

    @override_settings(BREVO_API_KEY='key')
    @patch('core.services.email_backends.BrevoEmailService.send_email')
    def test_send_transactional_success(self, mock_send):
        from core.services.email_backends import send_transactional_email
        mock_send.return_value = {'success': True, 'message_id': 'abc'}
        result = send_transactional_email(
            to_email='test@ex.com', subject='Test', html_content='<p>Hi</p>'
        )
        assert result['success'] is True

    @override_settings(BREVO_API_KEY=None)
    def test_send_simple_email_django_fallback(self):
        from core.services.email_backends import send_simple_email
        result = send_simple_email(
            to_email='test@ex.com', subject='Test', text_body='Hello',
            from_email='from@test.com',
        )
        assert result is True

    @override_settings(BREVO_API_KEY=None)
    def test_send_simple_email_with_html(self):
        from core.services.email_backends import send_simple_email
        result = send_simple_email(
            to_email='test@ex.com', subject='Test', text_body='Hello',
            html_body='<p>Hello</p>', from_email='from@test.com',
        )
        assert result is True

    @override_settings(BREVO_API_KEY=None)
    def test_send_simple_email_with_bcc(self):
        from core.services.email_backends import send_simple_email
        result = send_simple_email(
            to_email='test@ex.com', subject='Test', text_body='Hello',
            from_email='from@test.com', bcc=['bcc@test.com'],
        )
        assert result is True


# ==============================================================================
# DEVIS FORMS
# ==============================================================================

class TestDevisForms:
    def test_quote_request_form_import(self):
        from apps.devis.forms import QuoteRequestForm
        form = QuoteRequestForm()
        assert 'client_name' in form.fields or 'email' in form.fields

    def test_quote_request_form_fields(self):
        from apps.devis.forms import QuoteRequestForm
        form = QuoteRequestForm()
        assert 'client_name' in form.fields or 'email' in form.fields


# ==============================================================================
# DEVIS SERVICES
# ==============================================================================

@pytest.mark.django_db
class TestDevisServices:
    def test_generate_quote_number(self, devis_client):
        """Quote number is auto-generated on save."""
        q = Quote.objects.create(client=devis_client, status='draft')
        assert q.number.startswith('DEV-')


# ==============================================================================
# FACTURES UTILS/SERVICES
# ==============================================================================

class TestFacturesImports:
    def test_import_utils(self):
        from apps.factures import utils
        assert hasattr(utils, '__name__')

    def test_import_email_service(self):
        from apps.factures.services import email_service
        assert hasattr(email_service, '__name__')

    def test_import_pdf_generator(self):
        from apps.factures.services import pdf_generator
        assert hasattr(pdf_generator, '__name__')
