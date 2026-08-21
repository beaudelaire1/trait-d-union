"""Non-régression des constats P0 de l'audit du 21 août 2026."""
from __future__ import annotations

import base64
import json
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import Client, RequestFactory

from apps.devis import public_views as devis_public_views
from apps.factures import public_views as facture_public_views
from apps.leads.models import EmailSubscriber
from apps.simulateur.models import SimulatorReport
from apps.simulateur.p0_views import ReportSubmitP0View
from apps.simulateur.report_content_overrides import get_content_for


def test_public_contact_email_uses_studio_domain():
    html = render_to_string('partials/contact_email.html')
    marker = 'data-email="'
    encoded = html.split(marker, 1)[1].split('"', 1)[0]
    email = base64.b64decode(encoded).decode('utf-8')
    assert email == 'contact@traitdunion.studio'


@pytest.mark.django_db
def test_homepage_renders_delivery_metric_server_side():
    cache.clear()
    response = Client().get('/')
    assert response.status_code == 200
    html = response.content.decode('utf-8')
    assert 'data-target="100" data-suffix="%">100%</span>' in html
    assert 'data-target="100" data-suffix="%">0%</span>' not in html


@pytest.mark.django_db
def test_legal_page_matches_current_production_infrastructure():
    response = Client().get('/legal/')
    assert response.status_code == 200
    html = response.content.decode('utf-8')
    assert 'OVH SAS (OVHcloud)' in html
    assert 'Strasbourg' in html
    assert 'Django-Q2' in html
    assert 'Render Services, Inc.' not in html
    assert 'Hostinger International Ltd.' not in html
    assert 'Celery' not in html


@pytest.mark.django_db
def test_privacy_page_matches_infrastructure_and_transactional_report_use():
    response = Client().get('/confidentialite/')
    assert response.status_code == 200
    html = response.content.decode('utf-8')
    assert 'OVHcloud, Strasbourg, France' in html
    assert 'hébergement (Render)' not in html
    assert 'données de simulation' in html
    assert 'ne vous inscrit pas automatiquement à une newsletter' in html
    assert 'consentement distinct' in html


@pytest.mark.django_db
def test_simulator_report_ui_has_transactional_consent_only():
    response = Client().get('/simulateur/point-mort/')
    assert response.status_code == 200
    html = response.content.decode('utf-8')
    assert 'Attributs HTML :' not in html
    assert 'occasionnellement, du contenu utile' not in html
    assert (
        "J'accepte que mon adresse email soit utilisée pour me transmettre ce rapport."
        in html
    )
    assert 'Aucun abonnement marketing automatique' in html
    assert 'Pas d’inscription automatique' in html


@pytest.mark.django_db
def test_report_request_does_not_create_newsletter_subscriber():
    payload = {
        'email': 'direction@example.fr',
        'name': 'Direction',
        'company': 'Exemple',
        'tool_slug': 'point-mort',
        'tool_name': 'Seuil de Rentabilité',
        'snapshot': {'results': [], 'user_inputs': []},
        'consent': True,
        'website': '',
        'delivery': 'email',
    }
    client = Client()
    with patch.object(ReportSubmitP0View, '_dispatch_report_email') as dispatch:
        response = client.post(
            '/simulateur/report/',
            data=json.dumps(payload),
            content_type='application/json',
        )

    assert response.status_code == 200, response.content
    assert SimulatorReport.objects.filter(email='direction@example.fr').exists()
    assert not EmailSubscriber.objects.filter(email='direction@example.fr').exists()
    dispatch.assert_called_once()


def test_atterrissage_report_content_is_financial_not_onboarding():
    content = get_content_for('atterrissage')
    assert content['category'] == 'Pilotage financier'
    assert 'pipeline' in content['measures'].lower()
    assert 'marge' in content['measures'].lower()
    assert 'onboarding' not in content['measures'].lower()


def test_public_quote_pdf_is_private_and_no_store():
    request = RequestFactory().get('/devis/pdf/token/')
    upstream = HttpResponse(b'%PDF-test', content_type='application/pdf')
    with patch.object(devis_public_views, '_quote_public_pdf', return_value=upstream):
        response = devis_public_views.quote_public_pdf(request, 'token')

    assert response['Cache-Control'] == 'private, no-store, max-age=0'
    assert response['Pragma'] == 'no-cache'
    assert response['Expires'] == '0'


def test_public_invoice_pdf_is_private_and_no_store():
    request = RequestFactory().get('/factures/pdf/token/')
    upstream = HttpResponse(b'%PDF-test', content_type='application/pdf')
    with patch.object(facture_public_views, '_invoice_public_pdf', return_value=upstream):
        response = facture_public_views.invoice_public_pdf(request, 'token')

    assert response['Cache-Control'] == 'private, no-store, max-age=0'
    assert response['Pragma'] == 'no-cache'
    assert response['Expires'] == '0'