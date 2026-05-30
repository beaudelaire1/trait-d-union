"""Tests d'intégrité de la chaîne d'audit `InvoiceLifecycleEvent`.

Vérifie :
- création d'événement avec hash chaîné cohérent
- détection de tampering (modification d'un champ d'un événement passé)
- refus de l'UPDATE et du DELETE
- création automatique d'un événement DRAFT à la création de Invoice
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from apps.clients.models import ClientProfile
from apps.einvoicing.codelists import LifecycleState
from apps.einvoicing.models import InvoiceLifecycleEvent, GENESIS_HASH
from apps.factures.models import Invoice


pytestmark = pytest.mark.django_db


def _make_client() -> ClientProfile:
    return ClientProfile.objects.create(
        full_name="Acme SARL",
        email="acme@example.com",
        is_business=True,
        country_code="FR",
        siren="908264112",
    )


def _make_invoice() -> Invoice:
    inv = Invoice.objects.create(
        client=_make_client(),
        total_ht=Decimal("100.00"),
        tva=Decimal("0.00"),
        total_ttc=Decimal("100.00"),
        amount=Decimal("100.00"),
    )
    return inv


# ---------------------------------------------------------------------------
# Création automatique d'un événement DRAFT
# ---------------------------------------------------------------------------
class TestInvoiceLifecycleAutoCreate:
    def test_invoice_creation_emits_draft_event(self) -> None:
        inv = _make_invoice()
        events = list(InvoiceLifecycleEvent.objects.filter(invoice=inv))
        assert len(events) == 1
        assert events[0].state == LifecycleState.DRAFT
        assert events[0].previous_hash == GENESIS_HASH
        assert events[0].source == "invoice.created"

    def test_status_transition_emits_event(self) -> None:
        inv = _make_invoice()
        inv.status = "sent"
        inv.save()
        events = list(InvoiceLifecycleEvent.objects.filter(invoice=inv).order_by("occurred_at", "id"))
        assert len(events) == 2
        assert events[1].state == LifecycleState.SUBMITTED
        assert events[1].previous_hash == events[0].event_hash


# ---------------------------------------------------------------------------
# Immutabilité
# ---------------------------------------------------------------------------
class TestInvoiceLifecycleImmutability:
    def test_save_after_create_raises(self) -> None:
        inv = _make_invoice()
        ev = InvoiceLifecycleEvent.objects.filter(invoice=inv).first()
        assert ev is not None
        ev.source = "tampered"
        with pytest.raises(PermissionError):
            ev.save()

    def test_delete_raises(self) -> None:
        inv = _make_invoice()
        ev = InvoiceLifecycleEvent.objects.filter(invoice=inv).first()
        with pytest.raises(PermissionError):
            ev.delete()


# ---------------------------------------------------------------------------
# Vérification de chaîne
# ---------------------------------------------------------------------------
class TestInvoiceLifecycleChain:
    def test_chain_is_valid_on_creation(self) -> None:
        inv = _make_invoice()
        ok, broken = InvoiceLifecycleEvent.verify_chain(inv.pk)
        assert ok
        assert broken is None

    def test_chain_remains_valid_after_multiple_transitions(self) -> None:
        inv = _make_invoice()
        for new_status in ("sent", "partial", "paid"):
            inv.status = new_status
            inv.save()
        ok, broken = InvoiceLifecycleEvent.verify_chain(inv.pk)
        assert ok, f"chaîne cassée à l'événement {broken}"

    def test_tampering_breaks_chain(self) -> None:
        """Si un attaquant modifie un événement passé en DB (UPDATE direct),
        la fonction verify_chain doit le détecter."""
        inv = _make_invoice()
        ev = InvoiceLifecycleEvent.objects.filter(invoice=inv).first()
        # Bypass save() en passant par .update() pour simuler tampering DB
        InvoiceLifecycleEvent.objects.filter(pk=ev.pk).update(payload={"tampered": True})
        ok, broken = InvoiceLifecycleEvent.verify_chain(inv.pk)
        assert not ok
        assert broken == ev.pk


# ---------------------------------------------------------------------------
# Helper record() utilisable hors signaux
# ---------------------------------------------------------------------------
class TestInvoiceLifecycleRecord:
    def test_manual_record_chained(self) -> None:
        inv = _make_invoice()  # crée un DRAFT auto
        user = User.objects.create_user("ops", "ops@tus.local", "x")
        ev = InvoiceLifecycleEvent.record(
            invoice=inv,
            state=LifecycleState.SUBMITTED,
            actor=user,
            source="api.pdp.submit",
            payload={"pdp": "b2brouter", "external_id": "abc"},
        )
        assert ev.actor_id == user.pk
        assert ev.source == "api.pdp.submit"
        ok, _ = InvoiceLifecycleEvent.verify_chain(inv.pk)
        assert ok
