"""Tests for the leads app."""
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core import mail

from apps.leads.models import Lead, ProjectTypeChoice, BudgetRange
from apps.leads.forms import ContactForm
from apps.leads.services import EmailService
from apps.leads.views import verify_recaptcha


class VerifyRecaptchaTest(TestCase):
    """Test the verify_recaptcha function."""

    @override_settings(RECAPTCHA_SECRET_KEY='')
    def test_no_secret_key_passes(self):
        """Test that verification passes when no secret key is configured."""
        is_valid, score = verify_recaptcha('some-token', '127.0.0.1')
        self.assertTrue(is_valid)
        self.assertEqual(score, 1.0)

    @override_settings(RECAPTCHA_SECRET_KEY='test-secret')
    def test_no_token_passes(self):
        """Test that verification passes when token is empty (JS didn't load)."""
        is_valid, score = verify_recaptcha('', '127.0.0.1')
        self.assertTrue(is_valid)
        self.assertEqual(score, 1.0)

    @override_settings(RECAPTCHA_SECRET_KEY='test-secret', RECAPTCHA_SCORE_THRESHOLD=0.5)
    @patch('apps.leads.views.requests.post')
    def test_successful_verification_high_score(self, mock_post):
        """Test successful verification with high score."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'score': 0.9,
            'action': 'contact',
            'hostname': 'example.com'
        }
        mock_post.return_value = mock_response

        is_valid, score = verify_recaptcha('valid-token', '127.0.0.1')
        self.assertTrue(is_valid)
        self.assertEqual(score, 0.9)

    @override_settings(RECAPTCHA_SECRET_KEY='test-secret', RECAPTCHA_SCORE_THRESHOLD=0.5)
    @patch('apps.leads.views.requests.post')
    def test_low_score_fails(self, mock_post):
        """Test that low score fails verification."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'score': 0.3,
            'action': 'contact'
        }
        mock_post.return_value = mock_response

        is_valid, score = verify_recaptcha('valid-token', '127.0.0.1')
        self.assertFalse(is_valid)
        self.assertEqual(score, 0.3)

    @override_settings(RECAPTCHA_SECRET_KEY='test-secret')
    @patch('apps.leads.views.requests.post')
    def test_invalid_secret_passes(self, mock_post):
        """Test that invalid secret key error allows submission (graceful degradation)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': False,
            'error-codes': ['invalid-input-secret']
        }
        mock_post.return_value = mock_response

        is_valid, score = verify_recaptcha('some-token', '127.0.0.1')
        self.assertTrue(is_valid)
        self.assertEqual(score, 1.0)

    @override_settings(RECAPTCHA_SECRET_KEY='test-secret')
    @patch('apps.leads.views.requests.post')
    def test_wrong_action_fails(self, mock_post):
        """Test that wrong action name fails verification."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'score': 0.9,
            'action': 'login'  # Wrong action
        }
        mock_post.return_value = mock_response

        is_valid, score = verify_recaptcha('valid-token', '127.0.0.1', expected_action='contact')
        self.assertFalse(is_valid)
        self.assertEqual(score, 0.0)

    @override_settings(RECAPTCHA_SECRET_KEY='test-secret')
    @patch('apps.leads.views.requests.post')
    def test_network_error_passes(self, mock_post):
        """Test that network errors allow submission (graceful degradation)."""
        import requests as req
        mock_post.side_effect = req.RequestException("Connection timeout")

        is_valid, score = verify_recaptcha('some-token', '127.0.0.1')
        self.assertTrue(is_valid)
        self.assertEqual(score, 1.0)

    @override_settings(RECAPTCHA_SECRET_KEY='test-secret')
    @patch('apps.leads.views.requests.post')
    def test_timeout_handled(self, mock_post):
        """Test that API timeout is handled gracefully."""
        import requests as req
        mock_post.side_effect = req.Timeout("Request timed out")

        is_valid, score = verify_recaptcha('some-token', '127.0.0.1')
        self.assertTrue(is_valid)
        self.assertEqual(score, 1.0)


class LeadModelTest(TestCase):
    """Test the Lead model."""

    def test_lead_creation(self):
        """Test creating a lead with valid data."""
        lead = Lead.objects.create(
            name="Jean Dupont",
            email="jean@example.com",
            project_type=ProjectTypeChoice.VITRINE,
            message="Je souhaite un site vitrine pour mon entreprise.",
            budget=BudgetRange.MEDIUM,
        )
        self.assertEqual(lead.name, "Jean Dupont")
        self.assertEqual(lead.email, "jean@example.com")
        self.assertEqual(lead.project_type, ProjectTypeChoice.VITRINE)
        self.assertFalse(lead.is_processed)

    def test_lead_str(self):
        """Test the string representation of a lead."""
        lead = Lead.objects.create(
            name="Marie Martin",
            email="marie@example.com",
            project_type=ProjectTypeChoice.ECOMMERCE,
            message="Boutique en ligne",
        )
        self.assertEqual(str(lead), "Marie Martin – ecommerce")


class ContactFormTest(TestCase):
    """Test the contact form."""

    def test_valid_form(self):
        """Test that a form with valid data is valid."""
        form_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'project_type': ProjectTypeChoice.VITRINE,
            'message': 'Ceci est un message de test.',
            'budget': BudgetRange.SMALL,
            'honeypot': '',
        }
        form = ContactForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_honeypot_filled_invalid(self):
        """Test that a filled honeypot makes the form invalid."""
        form_data = {
            'name': 'Spammer',
            'email': 'spam@example.com',
            'project_type': ProjectTypeChoice.VITRINE,
            'message': 'Spam message',
            'honeypot': 'I am a bot',
        }
        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('honeypot', form.errors)

    def test_required_fields(self):
        """Test that required fields are enforced."""
        form = ContactForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('message', form.errors)


class ContactViewTest(TestCase):
    """Test the contact view."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('leads:contact')

    def test_contact_page_loads(self):
        """Test that the contact page loads successfully."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'leads/contact.html')

    def test_contact_form_in_context(self):
        """Test that the contact form is in the template context."""
        response = self.client.get(self.url)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], ContactForm)

    def test_successful_submission(self):
        """Test successful form submission creates a lead."""
        form_data = {
            'name': 'Test Submission',
            'email': 'submit@example.com',
            'project_type': ProjectTypeChoice.PLATEFORME,
            'message': 'Test submission message',
            'budget': BudgetRange.LARGE,
            'honeypot': '',
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(Lead.objects.filter(email='submit@example.com').exists())


class EmailServiceTest(TestCase):
    """Test email sending functionality."""

    def test_confirmation_email_sent(self):
        """Test that confirmation email is sent."""
        lead = Lead.objects.create(
            name="Email Test",
            email="email@test.com",
            project_type=ProjectTypeChoice.VITRINE,
            message="Testing email",
        )
        EmailService.send_confirmation_email(lead)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Merci de votre demande", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ['email@test.com'])

    def test_admin_notification_sent(self):
        """Test that admin notification is sent."""
        lead = Lead.objects.create(
            name="Admin Test",
            email="admin@test.com",
            project_type=ProjectTypeChoice.ECOMMERCE,
            message="Testing admin notification",
        )
        EmailService.send_admin_notification(lead)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Nouveau lead", mail.outbox[0].subject)


class ContactSuccessViewTest(TestCase):
    """Test the contact success view."""

    def test_success_page_loads(self):
        """Test that the success page loads."""
        response = self.client.get(reverse('leads:success'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'leads/success.html')
