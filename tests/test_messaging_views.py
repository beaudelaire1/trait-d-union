"""Tests for messaging views, leads email_views, chroniques, audit, dashboard, healthz."""
import json
import pytest
from unittest.mock import patch, MagicMock
from django.test import Client, RequestFactory
from django.contrib.auth.models import User

from apps.messaging.models import Prospect, EmailTemplate


@pytest.fixture
def staff_user(db):
    return User.objects.create_user('staff_msg', 'staff_msg@test.com', 'pass123', is_staff=True)


@pytest.fixture
def prospect(db):
    return Prospect.objects.create(
        email='prospect@test.com', contact_name='Jean Test',
        company_name='Test Co', status='new',
    )


@pytest.fixture
def email_template(db):
    return EmailTemplate.objects.create(
        name='Welcome', slug='welcome', subject='Welcome!',
        html_template='<p>Welcome {{name}}</p>', category='general',
    )


# ==============================================================================
# MESSAGING ACCESS CONTROL
# ==============================================================================

@pytest.mark.django_db
class TestMessagingAccess:
    def test_inbox_requires_staff(self, client):
        response = client.get('/tus-gestion-secure/messaging/')
        assert response.status_code == 302

    def test_compose_requires_staff(self, client):
        response = client.get('/tus-gestion-secure/messaging/compose/')
        assert response.status_code == 302

    def test_prospect_list_requires_staff(self, client):
        response = client.get('/tus-gestion-secure/messaging/prospects/')
        assert response.status_code == 302

    def test_campaign_list_requires_staff(self, client):
        response = client.get('/tus-gestion-secure/messaging/campaigns/')
        assert response.status_code == 302


# ==============================================================================
# MESSAGING VIEWS (STAFF)
# ==============================================================================

@pytest.mark.django_db
class TestMessagingInbox:
    def test_inbox_loads(self, client, staff_user):
        client.force_login(staff_user)
        response = client.get('/tus-gestion-secure/messaging/')
        assert response.status_code == 200

    def test_compose_loads(self, client, staff_user):
        client.force_login(staff_user)
        response = client.get('/tus-gestion-secure/messaging/compose/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestMessagingProspects:
    def test_prospect_list(self, client, staff_user, prospect):
        client.force_login(staff_user)
        response = client.get('/tus-gestion-secure/messaging/prospects/')
        assert response.status_code == 200

    def test_prospect_detail(self, client, staff_user, prospect):
        client.force_login(staff_user)
        response = client.get(f'/tus-gestion-secure/messaging/prospects/{prospect.pk}/')
        assert response.status_code == 200

    def test_prospect_create_get(self, client, staff_user):
        client.force_login(staff_user)
        response = client.get('/tus-gestion-secure/messaging/prospects/create/')
        assert response.status_code == 200

    def test_prospect_create_post(self, client, staff_user):
        client.force_login(staff_user)
        response = client.post('/tus-gestion-secure/messaging/prospects/create/', {
            'email': 'new@test.com',
            'contact_name': 'New Prospect',
            'company_name': 'New Co',
            'status': 'new',
        })
        assert response.status_code in (200, 302)

    def test_prospect_edit_get(self, client, staff_user, prospect):
        client.force_login(staff_user)
        response = client.get(f'/tus-gestion-secure/messaging/prospects/{prospect.pk}/edit/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestMessagingCampaigns:
    def test_campaign_list(self, client, staff_user):
        client.force_login(staff_user)
        response = client.get('/tus-gestion-secure/messaging/campaigns/')
        assert response.status_code == 200

    def test_campaign_create_get(self, client, staff_user):
        client.force_login(staff_user)
        response = client.get('/tus-gestion-secure/messaging/campaigns/create/')
        assert response.status_code == 200

    def test_template_list(self, client, staff_user, email_template):
        client.force_login(staff_user)
        response = client.get('/tus-gestion-secure/messaging/templates/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestMessagingImport:
    def test_import_post_empty(self, client, staff_user):
        client.force_login(staff_user)
        response = client.post('/tus-gestion-secure/messaging/prospects/import/')
        assert response.status_code in (200, 400)


@pytest.mark.django_db
class TestMessagingQuickAdd:
    def test_quick_add_post(self, client, staff_user):
        client.force_login(staff_user)
        response = client.post(
            '/tus-gestion-secure/messaging/api/prospects/quick-add/',
            json.dumps({
                'email': 'quick@test.com',
                'contact_name': 'Quick Add',
            }),
            content_type='application/json',
        )
        assert response.status_code in (200, 201)


@pytest.mark.django_db
class TestMessagingSendEmail:
    @patch('apps.messaging.views.send_prospect_email', return_value=True)
    def test_send_email_to_prospect(self, mock_send, client, staff_user, prospect):
        client.force_login(staff_user)
        response = client.post(f'/tus-gestion-secure/messaging/prospects/{prospect.pk}/send/', {
            'subject': 'Test Email',
            'body_html': 'Hello!',
        })
        assert response.status_code in (200, 302)


@pytest.mark.django_db
class TestSendEmailAPI:
    def test_send_email_api_requires_staff(self, client):
        response = client.post('/tus-gestion-secure/messaging/api/send/')
        assert response.status_code == 302

    @patch('apps.messaging.views.send_prospect_email', return_value=True)
    def test_send_email_api_post(self, mock_send, client, staff_user):
        client.force_login(staff_user)
        response = client.post(
            '/tus-gestion-secure/messaging/api/send/',
            json.dumps({
                'to': 'test@example.com',
                'subject': 'Test',
                'body': '<p>Hello</p>',
            }),
            content_type='application/json',
        )
        assert response.status_code in (200, 400)


# ==============================================================================
# MESSAGING MODELS
# ==============================================================================

@pytest.mark.django_db
class TestMessagingModels:
    def test_prospect_str(self, prospect):
        assert 'prospect@test.com' in str(prospect)

    def test_template_str(self, email_template):
        assert 'Welcome' in str(email_template)

    def test_campaign_creation(self, staff_user, db):
        from apps.messaging.models import EmailCampaign
        campaign = EmailCampaign.objects.create(
            name='Test Campaign', created_by=staff_user,
        )
        assert 'Test Campaign' in str(campaign)
        assert campaign.open_rate == 0
        assert campaign.click_rate == 0


# ==============================================================================
# MESSAGING SERVICES
# ==============================================================================

@pytest.mark.django_db
class TestMessagingServices:
    @patch('apps.messaging.services.send_mail')
    def test_send_prospect_email(self, mock_send, prospect):
        from apps.messaging.services import send_prospect_email
        result = send_prospect_email(prospect, 'Test Subject', '<p>Hi</p>')
        assert isinstance(result, dict)
        assert result.get('success') is True


# ==============================================================================
# LEADS EMAIL VIEWS
# ==============================================================================

@pytest.mark.django_db
class TestLeadsEmailViews:
    def test_email_compose_requires_staff(self, client):
        response = client.get('/tus-gestion-secure/emails/compose/')
        assert response.status_code == 302

    def test_email_list_requires_staff(self, client):
        response = client.get('/tus-gestion-secure/emails/')
        assert response.status_code == 302

    def test_email_compose_loads(self, client, staff_user):
        client.force_login(staff_user)
        response = client.get('/tus-gestion-secure/emails/compose/')
        assert response.status_code == 200

    def test_email_list_loads(self, client, staff_user):
        client.force_login(staff_user)
        response = client.get('/tus-gestion-secure/emails/')
        assert response.status_code == 200


# ==============================================================================
# CHRONIQUES
# ==============================================================================

@pytest.mark.django_db
class TestChroniquesViews:
    def test_chroniques_list(self, client):
        response = client.get('/chroniques/')
        assert response.status_code == 200

    def test_chroniques_nonexistent_detail(self, client):
        response = client.get('/chroniques/nonexistent-slug/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestChroniquesModels:
    def test_article_creation(self):
        from apps.chroniques.models import Article
        from django.utils import timezone
        article = Article.objects.create(
            title='Test Article', slug='test-article',
            body='Content here', is_published=True,
            publish_date=timezone.now(),
        )
        assert 'Test Article' in str(article)


# ==============================================================================
# AUDIT MODELS
# ==============================================================================

@pytest.mark.django_db
class TestAuditModels:
    def test_audit_log_creation(self):
        from apps.audit.models import AuditLog
        log = AuditLog.objects.create(
            action_type='quote_created',
            content_type='devis.Quote',
            object_id=1,
            description='Test log entry',
        )
        assert log.pk is not None

    def test_audit_log_str(self):
        from apps.audit.models import AuditLog
        log = AuditLog.objects.create(
            action_type='invoice_paid',
            content_type='factures.Invoice',
            object_id=42,
        )
        s = str(log)
        assert 'Invoice' in s or 'factures' in s

    def test_audit_log_action_classmethod(self, staff_user):
        from apps.audit.models import AuditLog
        log = AuditLog.log_action(
            action_type='client_account_created',
            actor=staff_user,
            content_type='auth.User',
            object_id=staff_user.pk,
            description='Created client',
        )
        assert log.pk is not None


# ==============================================================================
# PAGES DASHBOARD VIEWS
# ==============================================================================

@pytest.mark.django_db
class TestDashboardViews:
    def test_dashboard_requires_staff(self, client):
        response = client.get('/tus-gestion-secure/dashboard/')
        assert response.status_code == 302

    def test_dashboard_loads_for_staff(self, client, staff_user):
        client.force_login(staff_user)
        response = client.get('/tus-gestion-secure/dashboard/')
        assert response.status_code == 200


# ==============================================================================
# HEALTHZ
# ==============================================================================

@pytest.mark.django_db
class TestHealthzDetails:
    def test_healthz_returns_json(self, client):
        response = client.get('/healthz/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'status' in data


# ==============================================================================
# PORTFOLIO/RESOURCES IMPORTS
# ==============================================================================

class TestPortfolioImports:
    def test_portfolio_model_import(self):
        from apps.portfolio.models import Project
        assert hasattr(Project, 'objects')


class TestResourcesImports:
    def test_knowledge_article_model_import(self):
        from apps.resources.models import KnowledgeArticle
        assert hasattr(KnowledgeArticle, 'objects')

    def test_knowledge_category_model_import(self):
        from apps.resources.models import KnowledgeCategory
        assert hasattr(KnowledgeCategory, 'objects')
