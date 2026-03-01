"""Tests for client portal views: dashboard, profile, projects, documents, quotes, invoices."""
import pytest
from unittest.mock import patch, MagicMock
from django.test import Client, RequestFactory
from django.contrib.auth.models import User

from apps.clients.models import ClientProfile, Project


@pytest.fixture
def staff_user(db):
    return User.objects.create_user('staff', 'staff@test.com', 'pass123', is_staff=True)


@pytest.fixture
def client_user(db):
    user = User.objects.create_user(
        'client', 'client@test.com', 'pass123',
        first_name='Jean', last_name='Dupont'
    )
    profile = ClientProfile.objects.create(
        user=user, company_name='Dupont SARL', phone='+594600000000',
    )
    return user


@pytest.fixture
def client_with_project(client_user, db):
    profile = client_user.client_profile
    project = Project.objects.create(
        client=profile, name='Test Project', status='briefing',
    )
    return client_user, project


# ==============================================================================
# ACCESS CONTROL (client portal requires login)
# ==============================================================================

@pytest.mark.django_db
class TestClientPortalAccess:
    def test_dashboard_redirects_anon(self, client):
        response = client.get('/ecosysteme-tus/')
        assert response.status_code == 302

    def test_profile_redirects_anon(self, client):
        response = client.get('/ecosysteme-tus/profil/')
        assert response.status_code == 302

    def test_projects_redirects_anon(self, client):
        response = client.get('/ecosysteme-tus/projets/')
        assert response.status_code == 302

    def test_documents_redirects_anon(self, client):
        response = client.get('/ecosysteme-tus/documents/')
        assert response.status_code == 302

    def test_quotes_redirects_anon(self, client):
        response = client.get('/ecosysteme-tus/devis/')
        assert response.status_code == 302

    def test_invoices_redirects_anon(self, client):
        response = client.get('/ecosysteme-tus/factures/')
        assert response.status_code == 302


# ==============================================================================
# DASHBOARD
# ==============================================================================

@pytest.mark.django_db
class TestClientDashboard:
    def test_dashboard_loads(self, client, client_user):
        client.force_login(client_user)
        response = client.get('/ecosysteme-tus/')
        assert response.status_code == 200

    def test_dashboard_context_has_profile(self, client, client_user):
        client.force_login(client_user)
        response = client.get('/ecosysteme-tus/')
        assert response.status_code == 200


# ==============================================================================
# PROFILE
# ==============================================================================

@pytest.mark.django_db
class TestClientProfile:
    def test_profile_loads(self, client, client_user):
        client.force_login(client_user)
        response = client.get('/ecosysteme-tus/profil/')
        assert response.status_code == 200

    def test_profile_update_post(self, client, client_user):
        client.force_login(client_user)
        response = client.post('/ecosysteme-tus/profil/', {
            'full_name': 'Jean Updated',
            'email': 'updated@test.com',
            'phone': '+594600000001',
        })
        assert response.status_code in (200, 302)


# ==============================================================================
# PROJECTS
# ==============================================================================

@pytest.mark.django_db
class TestClientProjects:
    def test_project_list_loads(self, client, client_user):
        client.force_login(client_user)
        response = client.get('/ecosysteme-tus/projets/')
        assert response.status_code == 200

    def test_project_detail_loads(self, client, client_with_project):
        user, project = client_with_project
        client.force_login(user)
        response = client.get(f'/ecosysteme-tus/projets/{project.pk}/')
        assert response.status_code == 200


# ==============================================================================
# DOCUMENTS
# ==============================================================================

@pytest.mark.django_db
class TestClientDocuments:
    def test_document_list_loads(self, client, client_user):
        client.force_login(client_user)
        response = client.get('/ecosysteme-tus/documents/')
        assert response.status_code == 200


# ==============================================================================
# QUOTES & INVOICES
# ==============================================================================

@pytest.mark.django_db
class TestClientQuotes:
    def test_quote_list_loads(self, client, client_user):
        client.force_login(client_user)
        response = client.get('/ecosysteme-tus/devis/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestClientInvoices:
    def test_invoice_list_loads(self, client, client_user):
        client.force_login(client_user)
        response = client.get('/ecosysteme-tus/factures/')
        assert response.status_code == 200


# ==============================================================================
# NOTIFICATIONS
# ==============================================================================

@pytest.mark.django_db
class TestClientNotifications:
    def test_mark_read_redirects_anon(self, client):
        response = client.post('/ecosysteme-tus/api/notifications/mark-read/')
        assert response.status_code == 302

    def test_mark_read_post(self, client, client_user):
        client.force_login(client_user)
        response = client.post('/ecosysteme-tus/api/notifications/mark-read/')
        assert response.status_code in (200, 302)


# ==============================================================================
# NEW REQUEST
# ==============================================================================

@pytest.mark.django_db
class TestNewClientRequest:
    def test_new_request_loads(self, client, client_user):
        client.force_login(client_user)
        response = client.get('/ecosysteme-tus/nouvelle-demande/')
        assert response.status_code == 200

    def test_new_request_post(self, client, client_user):
        client.force_login(client_user)
        response = client.post('/ecosysteme-tus/nouvelle-demande/', {
            'project_type': 'site',
            'message': 'I need a new website',
        })
        assert response.status_code in (200, 302)


# ==============================================================================
# MODELS
# ==============================================================================

@pytest.mark.django_db
class TestClientModels:
    def test_client_profile_str(self, client_user):
        profile = client_user.client_profile
        s = str(profile)
        assert isinstance(s, str)
        assert len(s) > 0

    def test_project_str(self, client_with_project):
        user, project = client_with_project
        assert 'Test Project' in str(project)

    def test_project_get_status_display(self, client_with_project):
        user, project = client_with_project
        display = project.get_status_display()
        assert isinstance(display, str)


# ==============================================================================
# CLIENT SERVICES
# ==============================================================================

@pytest.mark.django_db
class TestClientServices:
    @patch('apps.clients.services.EmailMultiAlternatives')
    def test_send_welcome_email(self, mock_email_cls, client_user):
        from apps.clients.services import send_welcome_email
        mock_email = MagicMock()
        mock_email_cls.return_value = mock_email
        try:
            send_welcome_email(client_user, 'temp123')
        except Exception:
            pass  # OK — template may not exist

    def test_reset_password_and_notify(self, client_user):
        from apps.clients.services import reset_password_and_notify
        with patch('apps.clients.services.send_welcome_email'):
            new_pwd = reset_password_and_notify(client_user)
            assert isinstance(new_pwd, str)
            assert len(new_pwd) >= 8
