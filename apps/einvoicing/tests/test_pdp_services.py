"""Tests des services métier `submit_invoice_to_pdp` / `ingest_lifecycle_event`.

On utilise un faux PDPClient (pas de réseau).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import pytest

from apps.clients.models import ClientProfile
from apps.einvoicing.codelists import LifecycleState
from apps.einvoicing.models import InvoiceLifecycleEvent
from apps.einvoicing.pdp.base import PDPClient, PDPLifecycleEvent, PDPSubmission
from apps.einvoicing.pdp.exceptions import PDPValidationError
from apps.einvoicing.services import ingest_lifecycle_event, submit_invoice_to_pdp
from apps.factures.models import Invoice, InvoiceItem


pytestmark = pytest.mark.django_db


class _FakePDP(PDPClient):
    provider = "fake"

    def __init__(self, *, raise_validation: bool = False) -> None:
        self.raise_validation = raise_validation
        self.last_submitted: Optional[Invoice] = None

    def submit_invoice(self, invoice, *, facturx_pdf=None, cii_xml=None) -> PDPSubmission:
        if self.raise_validation:
            raise PDPValidationError("rejected", provider=self.provider, status_code=422)
        self.last_submitted = invoice
        return PDPSubmission(
            external_id="ext_123",
            state=LifecycleState.SUBMITTED,
            accepted_at=datetime.now(timezone.utc),
        )

    def get_lifecycle(self, external_id: str):
        return []

    def lookup_directory(self, sirenorsiret: str):
        return None


def _make_invoice() -> Invoice:
    client = ClientProfile.objects.create(full_name="X", email="x@y.fr")
    inv = Invoice.objects.create(client=client)
    InvoiceItem.objects.create(
        invoice=inv,
        description="X",
        quantity=Decimal("1"),
        unit_price=Decimal("100.00"),
        tax_rate=Decimal("0"),
    )
    inv.compute_totals()
    return inv


class TestSubmitToPDP:
    def test_success_persists_external_id_and_state(self) -> None:
        inv = _make_invoice()
        ev = submit_invoice_to_pdp(inv, client=_FakePDP())
        inv.refresh_from_db()
        assert inv.external_pdp_id == "ext_123"
        assert inv.lifecycle_state == LifecycleState.SUBMITTED
        assert ev.state == LifecycleState.SUBMITTED
        assert ev.source == "pdp.fake.submit"

    def test_validation_error_logs_rejected_event_and_reraises(self) -> None:
        inv = _make_invoice()
        with pytest.raises(PDPValidationError):
            submit_invoice_to_pdp(inv, client=_FakePDP(raise_validation=True))
        events = list(InvoiceLifecycleEvent.objects.filter(invoice=inv).order_by("-occurred_at"))
        # un DRAFT auto + un REJECTED
        assert any(e.state == LifecycleState.REJECTED for e in events)
        inv.refresh_from_db()
        # external_pdp_id reste vide (pas de soumission acceptée)
        assert inv.external_pdp_id == ""


class TestIngestLifecycle:
    def test_records_event_and_updates_state(self) -> None:
        inv = _make_invoice()
        ingest_lifecycle_event(
            inv, state=LifecycleState.DELIVERED, source="pdp.b2brouter.webhook",
            payload={"reason": "ok"},
        )
        inv.refresh_from_db()
        assert inv.lifecycle_state == LifecycleState.DELIVERED
        assert InvoiceLifecycleEvent.objects.filter(
            invoice=inv, state=LifecycleState.DELIVERED
        ).exists()
