"""Tests de l'adapter B2Brouter — sans appel réseau réel.

On mocke `requests.Session.request` pour valider le contrat HTTP.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

from apps.clients.models import ClientProfile
from apps.einvoicing.pdp.b2brouter import B2BrouterClient, STAGING_BASE
from apps.einvoicing.pdp.exceptions import (
    PDPAuthError,
    PDPRateLimitError,
    PDPValidationError,
    PDPTransportError,
)
from apps.factures.models import Invoice, InvoiceItem


pytestmark = pytest.mark.django_db


def _client_invoice() -> Invoice:
    client = ClientProfile.objects.create(
        full_name="Acme",
        email="acme@example.com",
        is_business=True,
        siren="908264112",
        country_code="FR",
    )
    inv = Invoice.objects.create(client=client)
    InvoiceItem.objects.create(
        invoice=inv,
        description="X",
        quantity=Decimal("1"),
        unit_price=Decimal("100.00"),
        tax_rate=Decimal("0"),
        vat_category_code="O",
        vat_exemption_reason_code="VATEX-EU-O",
    )
    inv.compute_totals()
    return inv


def _mock_response(status: int, json_body: dict | None = None, headers: dict | None = None):
    resp = MagicMock()
    resp.status_code = status
    resp.headers = headers or {}
    resp.content = b"{}" if json_body is None else b"{...}"
    resp.text = ""
    resp.json = lambda: (json_body or {})
    return resp


class TestB2BrouterAuth:
    def test_no_api_key_raises_auth_error(self) -> None:
        client = B2BrouterClient(api_key="", sandbox=True)
        inv = _client_invoice()
        # On bypass la génération facturx (testée ailleurs) en passant des bytes vides.
        with pytest.raises(PDPAuthError):
            client.submit_invoice(inv, facturx_pdf=b"%PDF-1.7\n")

    @patch("requests.Session.request")
    def test_401_raises_auth_error(self, mock_request) -> None:
        mock_request.return_value = _mock_response(401, {"error": "unauthorized"})
        client = B2BrouterClient(api_key="bad", sandbox=True)
        inv = _client_invoice()
        with pytest.raises(PDPAuthError):
            client.submit_invoice(inv, facturx_pdf=b"%PDF-1.7\n")


class TestB2BrouterSubmit:
    @patch("requests.Session.request")
    def test_submit_success(self, mock_request) -> None:
        mock_request.return_value = _mock_response(
            201,
            {"invoice": {"id": "inv_abc123", "state": "DEPOSEE", "created_at": "2026-05-29T18:00:00Z"}},
        )
        client = B2BrouterClient(api_key="ok", sandbox=True)
        inv = _client_invoice()
        sub = client.submit_invoice(inv, facturx_pdf=b"%PDF-1.7\n")
        assert sub.external_id == "inv_abc123"
        # DEPOSEE → SUBMITTED selon le mapping de normalisation
        assert sub.state == "SUBMITTED"

        # Vérifie que la requête HTTP est bien faite vers staging avec les headers
        called_args = mock_request.call_args
        assert called_args.kwargs["url"].startswith(STAGING_BASE)
        # Headers Session : on vérifie via session.headers (post-mount)
        # Note : Session.request reçoit method/url/json/params/timeout — pas headers ici.
        assert called_args.kwargs["method"] == "POST"

    @patch("requests.Session.request")
    def test_422_raises_validation(self, mock_request) -> None:
        mock_request.return_value = _mock_response(422, {"errors": ["invalid SIRET"]})
        client = B2BrouterClient(api_key="ok", sandbox=True)
        with pytest.raises(PDPValidationError):
            client.submit_invoice(_client_invoice(), facturx_pdf=b"%PDF-1.7\n")

    @patch("requests.Session.request")
    def test_429_raises_rate_limit(self, mock_request) -> None:
        mock_request.return_value = _mock_response(429, {}, {"Retry-After": "12"})
        client = B2BrouterClient(api_key="ok", sandbox=True)
        try:
            client.submit_invoice(_client_invoice(), facturx_pdf=b"%PDF-1.7\n")
        except PDPRateLimitError as exc:
            assert exc.retry_after == 12
        else:
            pytest.fail("PDPRateLimitError non levé")

    @patch("requests.Session.request")
    def test_5xx_raises_transport(self, mock_request) -> None:
        mock_request.return_value = _mock_response(503, {})
        client = B2BrouterClient(api_key="ok", sandbox=True)
        with pytest.raises(PDPTransportError):
            client.submit_invoice(_client_invoice(), facturx_pdf=b"%PDF-1.7\n")


class TestB2BrouterLifecycle:
    @patch("requests.Session.request")
    def test_get_lifecycle_normalizes_states(self, mock_request) -> None:
        mock_request.return_value = _mock_response(
            200,
            {"lifecycle_events": [
                {"invoice_id": "inv_x", "state": "DEPOSEE", "occurred_at": "2026-05-29T18:00:00Z"},
                {"invoice_id": "inv_x", "state": "APPROUVEE", "occurred_at": "2026-05-30T10:00:00Z"},
                {"invoice_id": "inv_x", "state": "ENCAISSEE", "occurred_at": "2026-06-15T09:00:00Z"},
            ]},
        )
        client = B2BrouterClient(api_key="ok", sandbox=True)
        events = client.get_lifecycle("inv_x")
        states = [e.state for e in events]
        assert states == ["SUBMITTED", "APPROVED", "PAID"]


class TestB2BrouterDirectory:
    @patch("requests.Session.request")
    def test_lookup_directory_returns_normalized_dict(self, mock_request) -> None:
        mock_request.return_value = _mock_response(
            200,
            {"records": [{"name": "Mairie de Cayenne", "tin_value": "21800003700017", "country": "FR"}]},
        )
        client = B2BrouterClient(api_key="ok", sandbox=True)
        result = client.lookup_directory("21800003700017")
        assert result is not None
        assert result["name"] == "Mairie de Cayenne"
        assert result["siret"] == "21800003700017"
        assert result["country_code"] == "FR"

    @patch("requests.Session.request")
    def test_lookup_directory_empty_returns_none(self, mock_request) -> None:
        mock_request.return_value = _mock_response(200, {"records": []})
        client = B2BrouterClient(api_key="ok", sandbox=True)
        assert client.lookup_directory("00000000000000") is None
