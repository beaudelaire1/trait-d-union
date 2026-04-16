"""Tests for the simulator report endpoint (email capture + PDF)."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from apps.simulateur.models import SimulatorReport


@pytest.mark.django_db
class TestSimulatorReportEndpoint:
    endpoint = '/simulateur/report/'

    def _payload(self, **overrides):
        base = {
            'email': 'dirigeant@acme.fr',
            'name': 'Jean Dupont',
            'company': 'Acme PME',
            'tool_slug': 'acse',
            'tool_name': 'Flux A.C.S.E',
            'snapshot': {
                'verdict': 'Flux fragile',
                'score': '5.2 / 10',
                'sections': [],
                'recommendations': ['Cartographier le tunnel commercial.'],
            },
            'consent': True,
            'website': '',
        }
        base.update(overrides)
        return base

    def test_happy_path_sends_email_and_persists(self):
        client = Client()
        with patch('apps.simulateur.services.SimulatorReportService.send') as mock_send:
            mock_send.return_value = None
            res = client.post(
                self.endpoint,
                data=json.dumps(self._payload()),
                content_type='application/json',
            )
        assert res.status_code == 200, res.content
        body = res.json()
        assert body['ok'] is True
        assert SimulatorReport.objects.filter(email='dirigeant@acme.fr').exists()
        mock_send.assert_called_once()

    def test_missing_consent_is_rejected(self):
        client = Client()
        res = client.post(
            self.endpoint,
            data=json.dumps(self._payload(consent=False)),
            content_type='application/json',
        )
        assert res.status_code == 400
        body = res.json()
        assert body['ok'] is False
        assert 'consent' in body.get('errors', {})

    def test_invalid_email_is_rejected(self):
        client = Client()
        res = client.post(
            self.endpoint,
            data=json.dumps(self._payload(email='not-an-email')),
            content_type='application/json',
        )
        assert res.status_code == 400

    def test_disposable_email_is_rejected(self):
        client = Client()
        res = client.post(
            self.endpoint,
            data=json.dumps(self._payload(email='x@mailinator.com')),
            content_type='application/json',
        )
        assert res.status_code == 400

    def test_honeypot_returns_fake_success_without_persisting(self):
        client = Client()
        res = client.post(
            self.endpoint,
            data=json.dumps(self._payload(website='http://spam.example')),
            content_type='application/json',
        )
        assert res.status_code == 200
        assert res.json()['ok'] is True
        assert not SimulatorReport.objects.exists()

    def test_get_is_not_allowed(self):
        client = Client()
        res = client.get(self.endpoint)
        assert res.status_code == 405
