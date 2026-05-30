"""Tests du module stripe_sync (enrichissement uniquement, pas PDP)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from apps.clients.models import ClientProfile
from apps.einvoicing.stripe_sync import (
    _detect_tax_id_type,
    ingest_stripe_customer_tax_ids,
    sync_client_to_stripe_customer,
)


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Détection des types de tax_id
# ---------------------------------------------------------------------------
class TestDetectTaxIdType:
    def test_eu_vat_french(self) -> None:
        assert _detect_tax_id_type("FR12345678901", "FR") == "eu_vat"

    def test_eu_vat_german(self) -> None:
        assert _detect_tax_id_type("DE123456789", "DE") == "eu_vat"

    def test_fr_vat_siret(self) -> None:
        assert _detect_tax_id_type("90826411200016", "FR") == "fr_vat"

    def test_fr_vat_siren(self) -> None:
        assert _detect_tax_id_type("908264112", "FR") == "fr_vat"

    def test_unknown_returns_none(self) -> None:
        assert _detect_tax_id_type("123", "FR") is None
        assert _detect_tax_id_type("", "") is None


# ---------------------------------------------------------------------------
# sync_client_to_stripe_customer — Stripe désactivé
# ---------------------------------------------------------------------------
class TestSyncWithoutStripe:
    @patch("apps.einvoicing.stripe_sync._stripe_or_none", return_value=None)
    def test_returns_none_when_stripe_not_configured(self, _mock) -> None:
        client = ClientProfile.objects.create(full_name="X", email="x@y.fr")
        assert sync_client_to_stripe_customer(client) is None


# ---------------------------------------------------------------------------
# sync_client_to_stripe_customer — Stripe mocké
# ---------------------------------------------------------------------------
class TestSyncWithMockedStripe:
    @patch("apps.einvoicing.stripe_sync._stripe_or_none")
    def test_creates_customer_first_time(self, mock_stripe_factory) -> None:
        sk = MagicMock()
        sk.Customer.create.return_value = {"id": "cus_test_123"}
        sk.Customer.list_tax_ids.return_value = {"data": []}
        mock_stripe_factory.return_value = sk

        client = ClientProfile.objects.create(
            full_name="Acme",
            email="acme@example.com",
            is_business=True,
            country_code="FR",
            siren="908264112",
            tva_number="FR91908264112",
        )
        cid = sync_client_to_stripe_customer(client)
        assert cid == "cus_test_123"
        client.refresh_from_db()
        assert client.stripe_customer_id == "cus_test_123"
        # 2 tax_ids potentiels : tva_number puis siren → ici les deux passent
        assert sk.Customer.create_tax_id.call_count >= 1

    @patch("apps.einvoicing.stripe_sync._stripe_or_none")
    def test_modifies_existing_customer(self, mock_stripe_factory) -> None:
        sk = MagicMock()
        sk.Customer.list_tax_ids.return_value = {"data": []}
        mock_stripe_factory.return_value = sk

        client = ClientProfile.objects.create(
            full_name="Acme",
            email="acme@example.com",
            stripe_customer_id="cus_existing",
        )
        cid = sync_client_to_stripe_customer(client)
        assert cid == "cus_existing"
        sk.Customer.modify.assert_called_once()
        sk.Customer.create.assert_not_called()


# ---------------------------------------------------------------------------
# ingest_stripe_customer_tax_ids — webhook handler
# ---------------------------------------------------------------------------
class TestIngestTaxIds:
    @patch("apps.einvoicing.stripe_sync._stripe_or_none")
    def test_remontee_siret_depuis_stripe(self, mock_stripe_factory) -> None:
        sk = MagicMock()
        sk.Customer.list_tax_ids.return_value = {
            "data": [
                {"type": "fr_vat", "value": "90826411200016"},
                {"type": "eu_vat", "value": "FR91908264112"},
            ]
        }
        mock_stripe_factory.return_value = sk

        client = ClientProfile.objects.create(
            full_name="Acme",
            email="acme@example.com",
            stripe_customer_id="cus_xyz",
        )
        result = ingest_stripe_customer_tax_ids("cus_xyz")
        assert result is not None
        client.refresh_from_db()
        assert client.siret == "90826411200016"
        assert client.siren == "908264112"
        assert client.tva_number == "FR91908264112"
        assert client.is_business is True
