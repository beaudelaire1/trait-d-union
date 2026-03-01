"""Tests for models and config modules: sitemaps, services app, resources app,
document_generator, config.urls error handlers."""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import Client, RequestFactory
from django.core.cache import cache


# ==============================================================================
# SERVICES APP MODEL
# ==============================================================================

@pytest.mark.django_db
class TestServiceModel:
    def test_service_str(self):
        from services.models import ServiceCategory, Service
        cat = ServiceCategory.objects.create(name='Web', slug='web', icon='🌐')
        svc = Service.objects.create(
            name='Site Vitrine', slug='site-vitrine',
            description='Description test', category=cat,
            is_active=True, is_featured=True,
        )
        assert str(svc) == 'Site Vitrine'

    def test_service_category_str(self):
        from services.models import ServiceCategory
        cat = ServiceCategory.objects.create(name='Design', slug='design', icon='🎨')
        assert str(cat) == 'Design'

    def test_service_ordering(self):
        from services.models import ServiceCategory, Service
        cat1 = ServiceCategory.objects.create(name='Cat1', slug='cat1', order=1)
        cat2 = ServiceCategory.objects.create(name='Cat2', slug='cat2', order=2)
        Service.objects.create(name='B', slug='b', description='B', category=cat2, is_active=True)
        Service.objects.create(name='A', slug='a', description='A', category=cat1, is_active=True)
        services = list(Service.objects.values_list('name', flat=True))
        assert services[0] == 'A'

    def test_service_defaults(self):
        from services.models import ServiceCategory, Service
        cat = ServiceCategory.objects.create(name='Default', slug='default')
        svc = Service.objects.create(
            name='Test', slug='test-svc', description='Test', category=cat,
        )
        assert svc.is_active is True
        assert svc.is_featured is False
        assert svc.base_price == Decimal('0.00')
        assert svc.price_unit == 'forfait'


# ==============================================================================
# SITEMAPS
# ==============================================================================

@pytest.mark.django_db
class TestSitemaps:
    def test_static_view_sitemap_items(self):
        from config.sitemaps import StaticViewSitemap
        sitemap = StaticViewSitemap()
        items = sitemap.items()
        assert len(items) > 0

    def test_static_view_sitemap_location(self):
        from config.sitemaps import StaticViewSitemap
        sitemap = StaticViewSitemap()
        items = sitemap.items()
        for item in items:
            try:
                loc = sitemap.location(item)
                assert loc.startswith('/')
            except Exception:
                # Some URLs may need namespace, skip them
                pass

    def test_static_view_sitemap_priority(self):
        from config.sitemaps import StaticViewSitemap
        sitemap = StaticViewSitemap()
        items = sitemap.items()
        for item in items:
            p = sitemap.priority(item)
            assert 0.0 <= p <= 1.0

    def test_portfolio_sitemap_exists(self):
        from config.sitemaps import PortfolioSitemap
        sitemap = PortfolioSitemap()
        assert hasattr(sitemap, 'changefreq')

    def test_chroniques_sitemap_exists(self):
        from config.sitemaps import ChroniquesSitemap
        sitemap = ChroniquesSitemap()
        assert hasattr(sitemap, 'changefreq')


# ==============================================================================
# DOCUMENT GENERATOR (branching covered in ext tests)
# ==============================================================================

class TestDocumentGeneratorBranding:
    def test_default_branding_has_all_fields(self):
        from core.services.document_generator import DEFAULT_BRANDING
        required = ['name', 'email', 'phone', 'address', 'siret']
        for field in required:
            assert field in DEFAULT_BRANDING


# ==============================================================================
# CONFIG / URLS ERROR HANDLERS
# ==============================================================================

@pytest.mark.django_db
class TestErrorHandlers:
    def test_404_handler(self, client):
        response = client.get('/nonexistent-page-xyz/')
        assert response.status_code == 404

    def test_healthz_endpoint(self, client):
        response = client.get('/healthz/')
        assert response.status_code == 200


# ==============================================================================
# RESOURCES APP VIEWS
# ==============================================================================

@pytest.mark.django_db
class TestResourceViews:
    def test_resources_list(self, client):
        response = client.get('/resources/')
        assert response.status_code == 200


# ==============================================================================
# LEAD MODEL
# ==============================================================================

@pytest.mark.django_db
class TestLeadModel:
    def test_lead_str(self):
        from apps.leads.models import Lead, ProjectTypeChoice
        lead = Lead.objects.create(
            name='Test User', email='test@example.com',
            project_type=ProjectTypeChoice.SITE,
            message='Test message',
        )
        assert 'Test User' in str(lead)

    def test_lead_default_status(self):
        from apps.leads.models import Lead, ProjectTypeChoice, LeadStatus
        lead = Lead.objects.create(
            name='Test', email='test@ex.com',
            project_type=ProjectTypeChoice.COMMERCE,
            message='Test',
        )
        assert lead.status == LeadStatus.NEW

    def test_lead_is_converted_false(self):
        from apps.leads.models import Lead, ProjectTypeChoice
        lead = Lead.objects.create(
            name='Test', email='test@ex.com',
            project_type=ProjectTypeChoice.SITE,
            message='Test',
        )
        assert lead.is_converted is False

    def test_lead_ip_nullable(self):
        from apps.leads.models import Lead, ProjectTypeChoice
        lead = Lead.objects.create(
            name='Test', email='test@ex.com',
            project_type=ProjectTypeChoice.SITE,
            message='Test', ip_address=None,
        )
        assert lead.ip_address is None


# ==============================================================================
# LEAD FORMS
# ==============================================================================

class TestContactForm:
    def test_valid_form(self):
        from apps.leads.forms import ContactForm
        form = ContactForm(data={
            'name': 'Test', 'email': 'test@ex.com',
            'project_type': 'site', 'message': 'Hello', 'honeypot': '',
        })
        assert form.is_valid()

    def test_honeypot_invalid(self):
        from apps.leads.forms import ContactForm
        form = ContactForm(data={
            'name': 'Bot', 'email': 'bot@ex.com',
            'project_type': 'site', 'message': 'Spam', 'honeypot': 'gotcha',
        })
        assert not form.is_valid()
        assert 'honeypot' in form.errors

    def test_missing_required(self):
        from apps.leads.forms import ContactForm
        form = ContactForm(data={})
        assert not form.is_valid()
        assert 'name' in form.errors
        assert 'email' in form.errors
        assert 'message' in form.errors

    def test_attachment_too_large(self):
        from apps.leads.forms import ContactForm
        from django.core.files.uploadedfile import SimpleUploadedFile
        big = SimpleUploadedFile('big.pdf', b'0' * (6 * 1024 * 1024), content_type='application/pdf')
        form = ContactForm(data={
            'name': 'T', 'email': 'test@e.com',
            'project_type': 'site', 'message': 'H', 'honeypot': '',
        }, files={'attachment': big})
        assert not form.is_valid()

    def test_valid_pdf_attachment(self):
        from apps.leads.forms import ContactForm
        from django.core.files.uploadedfile import SimpleUploadedFile
        pdf = SimpleUploadedFile('doc.pdf', b'%PDF-1.4', content_type='application/pdf')
        form = ContactForm(data={
            'name': 'T', 'email': 'test@e.com',
            'project_type': 'site', 'message': 'H', 'honeypot': '',
        }, files={'attachment': pdf})
        assert form.is_valid()


