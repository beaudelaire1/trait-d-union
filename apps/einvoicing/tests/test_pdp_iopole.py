"""Tests de l'adapter IOPOLE — sans appel réseau réel.

On mocke `requests.Session.request` et `requests.Session.post` pour valider :
- le flux OAuth2 client_credentials et le cache du jeton ;
- les codes d'erreur HTTP (401, 422, 429, 5xx) ;
- la normalisation des états du cycle de vie ;
- l'annuaire SIREN/SIRET.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from apps.clients.models import ClientProfile
from apps.einvoicing.pdp.exceptions import (
    PDPAuthError,
    PDPRateLimitError,
    PDPTransportError,
    PDPValidationError,
)
from apps.einvoicing.pdp.iopole import IopoleClient, SANDBOX_BASE
from apps.factures.models import Invoice, InvoiceItem


pytestmark = pytest.mark.django_db


# ─── helpers ─────────────────────────────────────────────────────────────
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


def _make_client(**overrides) -> IopoleClient:
    """Crée un client IOPOLE avec valeurs par défaut + overrides."""
    defaults = {
        "sandbox": True,
        "client_id": "tus-cid",
        "client_secret": "tus-secret",
    }
    defaults.update(overrides)
    return IopoleClient(**defaults)


def _ok_token(expires_in: int = 3600):
    return _mock_response(200, {"access_token": "TKN", "expires_in": expires_in})


# ─── tests Auth ──────────────────────────────────────────────────────────
class TestIopoleAuth:
    def test_no_credentials_raises_auth_error(self) -> None:
        client = IopoleClient(client_id="", client_secret="", sandbox=True)
        with pytest.raises(PDPAuthError):
            client.submit_invoice(_client_invoice(), facturx_pdf=b"%PDF-1.7\n")

    @patch("requests.Session.post")
    @patch("requests.Session.request")
    def test_401_on_oauth_raises_auth_error(self, mock_request, mock_post) -> None:
        mock_post.return_value = _mock_response(401, {"error": "invalid_client"})
        client = _make_client()
        with pytest.raises(PDPAuthError):
            client.submit_invoice(_client_invoice(), facturx_pdf=b"%PDF-1.7\n")
        # le token endpoint doit être appelé une seule fois
        assert mock_post.call_count == 1
        assert mock_request.call_count == 0

    @patch("requests.Session.post")
    @patch("requests.Session.request")
    def test_token_is_cached_between_calls(self, mock_request, mock_post) -> None:
        mock_post.return_value = _ok_token(expires_in=3600)
        mock_request.return_value = _mock_response(
            201,
            {"invoice": {"id": "i1", "state": "DEPOSEE", "created_at": "2026-05-29T18:00:00Z"}},
        )
        client = _make_client()
        client.submit_invoice(_client_invoice(), facturx_pdf=b"%PDF-1.7\n")
        client.get_lifecycle("i1")
        # Le token n'est demandé qu'une fois
        assert mock_post.call_count == 1
        assert mock_request.call_count == 2


# ─── tests Submit ────────────────────────────────────────────────────────
class TestIopoleSubmit:
    @patch("requests.Session.post")
    @patch("requests.Session.request")
    def test_submit_success_targets_sandbox_v1(self, mock_request, mock_post) -> None:
        mock_post.return_value = _ok_token()
        mock_request.return_value = _mock_response(
            201,
            {"invoice": {"id": "iop_abc", "state": "DEPOSEE", "created_at": "2026-05-29T18:00:00Z"}},
        )
        client = _make_client()
        sub = client.submit_invoice(_client_invoice(), facturx_pdf=b"%PDF-1.7\n")
        assert sub.external_id == "iop_abc"
        assert sub.state == "SUBMITTED"  # DEPOSEE -> SUBMITTED
        called = mock_request.call_args
        assert called.kwargs["method"] == "POST"
        assert called.kwargs["url"].startswith(SANDBOX_BASE)
        assert called.kwargs["url"].endswith("/v1/invoices")
        # Bearer token bien posé
        assert called.kwargs["headers"]["Authorization"] == "Bearer TKN"

    @patch("requests.Session.post")
    @patch("requests.Session.request")
    def test_422_raises_validation(self, mock_request, mock_post) -> None:
        mock_post.return_value = _ok_token()
        mock_request.return_value = _mock_response(422, {"errors": ["invalid SIRET"]})
        client = _make_client()
        with pytest.raises(PDPValidationError):
            client.submit_invoice(_client_invoice(), facturx_pdf=b"%PDF-1.7\n")

    @patch("requests.Session.post")
    @patch("requests.Session.request")
    def test_429_raises_rate_limit(self, mock_request, mock_post) -> None:
        mock_post.return_value = _ok_token()
        mock_request.return_value = _mock_response(429, {}, {"Retry-After": "12"})
        client = _make_client()
        try:
            client.submit_invoice(_client_invoice(), facturx_pdf=b"%PDF-1.7\n")
        except PDPRateLimitError as exc:
            assert exc.retry_after == 12
        else:
            pytest.fail("PDPRateLimitError non levé")

    @patch("requests.Session.post")
    @patch("requests.Session.request")
    def test_5xx_raises_transport(self, mock_request, mock_post) -> None:
        mock_post.return_value = _ok_token()
        mock_request.return_value = _mock_response(503, {})
        client = _make_client()
        with pytest.raises(PDPTransportError):
            client.submit_invoice(_client_invoice(), facturx_pdf=b"%PDF-1.7\n")

    @patch("requests.Session.post")
    @patch("requests.Session.request")
    def test_401_then_retry_once_with_fresh_token(self, mock_request, mock_post) -> None:
        # 1er token, puis le serveur rejette (401), on force un refresh, 2e token
        mock_post.side_effect = [_ok_token(), _ok_token()]
        mock_request.side_effect = [
            _mock_response(401, {"error": "expired"}),
            _mock_response(
                201,
                {"invoice": {"id": "iop_z", "state": "DEPOSEE", "created_at": "2026-05-29T18:00:00Z"}},
            ),
        ]
        client = _make_client()
        sub = client.submit_invoice(_client_invoice(), facturx_pdf=b"%PDF-1.7\n")
        assert sub.external_id == "iop_z"
        assert mock_post.call_count == 2
        assert mock_request.call_count == 2


# ─── tests Lifecycle / Directory ─────────────────────────────────────────
class TestIopoleLifecycle:
    @patch("requests.Session.post")
    @patch("requests.Session.request")
    def test_get_lifecycle_normalizes_states(self, mock_request, mock_post) -> None:
        mock_post.return_value = _ok_token()
        mock_request.return_value = _mock_response(
            200,
            {"lifecycle_events": [
                {"invoice_id": "iop_x", "state": "DEPOSEE", "occurred_at": "2026-05-29T18:00:00Z"},
                {"invoice_id": "iop_x", "state": "APPROUVEE", "occurred_at": "2026-05-30T10:00:00Z"},
                {"invoice_id": "iop_x", "state": "ENCAISSEE", "occurred_at": "2026-06-15T09:00:00Z"},
            ]},
        )
        client = _make_client()
        events = client.get_lifecycle("iop_x")
        assert [e.state for e in events] == ["SUBMITTED", "APPROVED", "PAID"]


class TestIopoleDirectory:
    @patch("requests.Session.post")
    @patch("requests.Session.request")
    def test_lookup_directory(self, mock_request, mock_post) -> None:
        mock_post.return_value = _ok_token()
        mock_request.return_value = _mock_response(
            200,
            {"records": [{"name": "Mairie de Cayenne", "siret": "21800003700017", "country_code": "FR"}]},
        )
        client = _make_client()
        result = client.lookup_directory("21800003700017")
        assert result is not None
        assert result["name"] == "Mairie de Cayenne"
        assert result["siret"] == "21800003700017"
        assert result["country_code"] == "FR"

    @patch("requests.Session.post")
    @patch("requests.Session.request")
    def test_lookup_directory_empty_returns_none(self, mock_request, mock_post) -> None:
        mock_post.return_value = _ok_token()
        mock_request.return_value = _mock_response(200, {"records": []})
        client = _make_client()
        assert client.lookup_directory("00000000000000") is None
