"""Tests pour la validation des devis et onboarding client."""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date

from apps.devis.models import Quote
from apps.devis.application.validate_quote_usecase import (
    validate_quote,
    provision_client_account,
    QuoteValidationError,
    ClientAccountProvisionError,
)
from apps.clients.models import ClientProfile
from apps.audit.models import AuditLog


class ValidateQuoteUseCaseTestCase(TestCase):
    """Tests pour ValidateQuoteUseCase."""
    
    def setUp(self):
        """Setup de test."""
        self.user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.client_contact = ClientProfile.objects.create(
            full_name='Test Client',
            email='client@test.com',
            phone='+336',
        )
        
        self.quote = Quote.objects.create(
            client=self.client_contact,
            status=Quote.QuoteStatus.SENT,
            total_ttc=Decimal('1000.00'),
            issue_date=date.today(),
        )
    
    def test_validate_quote_changes_status(self):
        """Valider un devis change le statut."""
        result = validate_quote(
            self.quote,
            self.user,
            comment="Devis validé par admin"
        )
        
        # Vérifier le résultat
        self.assertIsNotNone(result.validated_at)
        self.assertEqual(result.validated_by, self.user)
        
        # Vérifier la base de données
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, Quote.QuoteStatus.VALIDATED)
        self.assertEqual(self.quote.validated_by, self.user)
    
    def test_validate_quote_creates_audit_log(self):
        """Valider un devis crée une entrée d'audit."""
        validate_quote(self.quote, self.user, comment="Test")
        
        # Vérifier l'entrée d'audit
        audit_log = AuditLog.objects.filter(
            action_type=AuditLog.ActionType.QUOTE_VALIDATED,
            object_id=self.quote.pk,
        ).first()
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.actor, self.user)
        self.assertEqual(audit_log.content_type, 'devis.Quote')
    
    def test_validate_non_sent_quote_fails(self):
        """Valider un devis non-SENT lève une erreur."""
        self.quote.status = Quote.QuoteStatus.DRAFT
        self.quote.save()
        
        with self.assertRaises(QuoteValidationError):
            validate_quote(self.quote, self.user)
    
    def test_validate_quote_with_request(self):
        """Valider un devis avec request enregistre IP/UserAgent."""
        factory = RequestFactory()
        request = factory.get('/', HTTP_X_FORWARDED_FOR='192.168.1.1')
        
        result = validate_quote(self.quote, self.user, request=request)
        
        self.assertIn('ip', result.audit_trail)
        self.assertEqual(result.audit_trail['ip'], '192.168.1.1')


class ProvisionClientAccountTestCase(TestCase):
    """Tests pour ProvisionClientAccountUseCase."""
    
    def setUp(self):
        """Setup de test."""
        self.client_contact = ClientProfile.objects.create(
            full_name='New Client',
            email='newclient@test.com',
            phone='+336',
            company_name='ACME Corp',
        )
        
        self.quote = Quote.objects.create(
            client=self.client_contact,
            status=Quote.QuoteStatus.VALIDATED,
            total_ttc=Decimal('1000.00'),
            issue_date=date.today(),
        )
    
    def test_provision_creates_new_user_and_profile(self):
        """Provision crée un nouveller User et ClientProfile."""
        result = provision_client_account(self.quote)
        
        # Vérifier que le compte est créé
        self.assertTrue(result.is_new)
        self.assertIsNotNone(result.temporary_password)
        self.assertEqual(result.user.email, self.client_contact.email)
        self.assertIsNotNone(result.client_profile)
    
    def test_provision_skips_existing_user(self):
        """Provision d'un devis avec compte existant skip la création."""
        # Créer un user existant
        existing_user = User.objects.create_user(
            username='existing',
            email=self.client_contact.email,
            password='testpass'
        )
        
        result = provision_client_account(self.quote)
        
        # Ne devrait pas créer de nouvel utilisateur
        self.assertFalse(result.is_new)
        self.assertEqual(result.user.pk, existing_user.pk)
    
    def test_provision_without_quote_client_fails(self):
        """Provision sans client lève une erreur."""
        # Créer un devis sans client pour tester
        # Note: Quote.client is NOT NULL, donc on teste avec None en mémoire
        quote_no_client = Quote(
            status=Quote.QuoteStatus.VALIDATED,
            total_ttc=Decimal('1000.00'),
            issue_date=date.today(),
        )
        
        with self.assertRaises(ClientAccountProvisionError):
            provision_client_account(quote_no_client)
    
    def test_provision_creates_audit_log(self):
        """Provision crée une entrée d'audit."""
        result = provision_client_account(self.quote)
        
        if result.is_new:
            audit_log = AuditLog.objects.filter(
                action_type=AuditLog.ActionType.CLIENT_ACCOUNT_CREATED,
                object_id=result.user.pk,
            ).first()
            
            self.assertIsNotNone(audit_log)
            self.assertIn('email', audit_log.metadata)
