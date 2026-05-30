"""Tests bout-en-bout du endpoint webhook B2Brouter (pas de réseau)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from decimal import Decimal

import pytest
from django.test import Client

from apps.clients.models import ClientProfile
from apps.einvoicing.codelists import LifecycleState
from apps.factures.models import Invoice, InvoiceItem


pytestmark = pytest.mark.django_db


SECRET = "whsec_unit_test"


@pytest.fixture(autouse=True)
def _configure_pdp(settings):
    settings.INVOICING = {
        "PDP": {
            "WEBHOOK_SECRET": SECRET,
            "PROVIDER": "b2brouter",
            "SANDBOX": True,
        },
    }


def _signed_post(body: dict, secret: str = SECRET):
    raw = json.dumps(body).encode("utf-8")
    ts = int(time.time())
    sig = hmac.new(secret.encode("utf-8"), f"{ts}.".encode("utf-8") + raw, hashlib.sha256).hexdigest()
    header = f"t={ts},s={sig}"
    return raw, header


def _make_invoice(external_id: str = "inv_xyz") -> Invoice:
    client = ClientProfile.objects.create(full_name="X", email="x@y.fr")
    inv = Invoice.objects.create(client=client)
    InvoiceItem.objects.create(
        invoice=inv, description="X", quantity=Decimal("1"),
        unit_price=Decimal("100.00"), tax_rate=Decimal("0"),
    )
    inv.compute_totals()
    inv.external_pdp_id = external_id
    inv.save(update_fields=["external_pdp_id"])
    return inv


URL = "/einvoicing/webhooks/b2brouter/"


def test_invalid_signature_returns_403() -> None:
    c = Client()
    body = json.dumps({"event": "invoice.delivered", "data": {"id": "inv_xyz"}}).encode("utf-8")
    resp = c.post(
        URL, body,
        content_type="application/json",
        HTTP_X_B2BROUTER_SIGNATURE="t=1,s=deadbeef",
    )
    assert resp.status_code == 403


def test_valid_signature_updates_invoice_state() -> None:
    inv = _make_invoice("inv_xyz")
    body = {"event": "invoice.delivered", "data": {"id": "inv_xyz", "state": "DELIVERED"}}
    raw, header = _signed_post(body)
    c = Client()
    resp = c.post(URL, raw, content_type="application/json", HTTP_X_B2BROUTER_SIGNATURE=header)
    assert resp.status_code == 204
    inv.refresh_from_db()
    assert inv.lifecycle_state == LifecycleState.DELIVERED


def test_unknown_invoice_returns_204() -> None:
    body = {"event": "invoice.delivered", "data": {"id": "inv_unknown", "state": "DELIVERED"}}
    raw, header = _signed_post(body)
    c = Client()
    resp = c.post(URL, raw, content_type="application/json", HTTP_X_B2BROUTER_SIGNATURE=header)
    assert resp.status_code == 204
