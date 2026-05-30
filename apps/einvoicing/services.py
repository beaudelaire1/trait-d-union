"""Services métier e-invoicing — passerelle entre Invoice et la PDP.

Garantit :
- la chaîne d'audit `InvoiceLifecycleEvent` est mise à jour pour TOUTE
  interaction avec la PDP (succès comme échec) ;
- les erreurs PDP sont normalisées via `apps.einvoicing.pdp.exceptions` ;
- l'identifiant externe PDP est stocké dans `Invoice.external_pdp_id`.

Ce module ne dépend pas de Django Q (pour rester testable) ; les jobs
async sont définis dans `apps.einvoicing.tasks`.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .codelists import LifecycleState
from .models import InvoiceLifecycleEvent
from .pdp import PDPClient, PDPError, get_pdp_client

if TYPE_CHECKING:  # pragma: no cover
    from apps.factures.models import Invoice

logger = logging.getLogger(__name__)


def submit_invoice_to_pdp(
    invoice: "Invoice",
    *,
    actor=None,
    client: PDPClient | None = None,
) -> InvoiceLifecycleEvent:
    """Soumet une facture à la PDP active et journalise l'événement.

    Renvoie l'événement enregistré (succès ou échec). En cas d'erreur PDP,
    un événement REJECTED est tracé avec le motif et l'erreur est relancée.
    """
    pdp = client or get_pdp_client()
    try:
        submission = pdp.submit_invoice(invoice)
    except PDPError as exc:
        logger.exception("PDP %s : échec soumission Invoice #%s", pdp.provider, invoice.pk)
        InvoiceLifecycleEvent.record(
            invoice=invoice,
            state=LifecycleState.REJECTED,
            actor=actor,
            source=f"pdp.{pdp.provider}.submit",
            payload={
                "error_class": type(exc).__name__,
                "status_code": getattr(exc, "status_code", None),
                "message": str(exc)[:1000],
            },
        )
        raise

    # Persistance de l'identifiant externe
    invoice.external_pdp_id = submission.external_id
    invoice.lifecycle_state = submission.state
    invoice.save(update_fields=["external_pdp_id", "lifecycle_state"])

    return InvoiceLifecycleEvent.record(
        invoice=invoice,
        state=submission.state,
        actor=actor,
        source=f"pdp.{pdp.provider}.submit",
        payload={
            "external_id": submission.external_id,
            "accepted_at": submission.accepted_at.isoformat(),
        },
    )


def ingest_lifecycle_event(
    invoice: "Invoice",
    *,
    state: str,
    source: str = "pdp.webhook",
    payload: dict | None = None,
) -> InvoiceLifecycleEvent:
    """Crée un lifecycle event à partir d'un signal externe (webhook PDP)
    et met à jour `invoice.lifecycle_state`."""
    payload = payload or {}
    event = InvoiceLifecycleEvent.record(
        invoice=invoice,
        state=state,
        source=source,
        payload=payload,
    )
    if invoice.lifecycle_state != state:
        invoice.lifecycle_state = state
        invoice.save(update_fields=["lifecycle_state"])
    return event


__all__ = ["submit_invoice_to_pdp", "ingest_lifecycle_event"]
