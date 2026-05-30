"""
Signaux einvoicing — bootstrap minimal Phase 1.

Pour l'instant, on enregistre :
- post_save sur `factures.Invoice` (création) → événement DRAFT initial.
- pre_save sur `factures.Invoice` (changement de status) → événement de transition.

Ceci garantit que toute facture du système possède une chaîne d'audit dès sa
création, même si la facture est créée hors de l'API e-invoicing (admin, devis
converti, fixture, script, etc.).

Aucune écriture sur le modèle Invoice : seules des entrées dans
InvoiceLifecycleEvent sont créées.
"""

from __future__ import annotations

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


# Mapping des status historiques de Invoice vers LifecycleState public.
# Reste tolérant : un status non mappé est simplement loggué et n'empêche
# pas l'enregistrement.
def _map_invoice_status_to_lifecycle(status: str) -> str | None:
    from .codelists import LifecycleState

    mapping = {
        "draft": LifecycleState.DRAFT,
        "demo": LifecycleState.DRAFT,
        "refacturation": LifecycleState.DRAFT,
        "sent": LifecycleState.SUBMITTED,
        "paid": LifecycleState.PAID,
        "partial": LifecycleState.SENT,  # encaissement partiel = considérée transmise
        "overdue": LifecycleState.SENT,
        "avoir": LifecycleState.ARCHIVED,
    }
    return mapping.get(status)


@receiver(pre_save, sender="factures.Invoice", dispatch_uid="einvoicing_invoice_pre_save")
def _capture_old_status(sender, instance, **kwargs):
    """Capture l'ancien status pour détecter une transition en post_save."""
    if not instance.pk:
        instance._einvoicing_old_status = None
        return
    try:
        old = sender.objects.only("status").get(pk=instance.pk)
        instance._einvoicing_old_status = old.status
    except sender.DoesNotExist:
        instance._einvoicing_old_status = None


@receiver(post_save, sender="factures.Invoice", dispatch_uid="einvoicing_invoice_post_save")
def _record_lifecycle_event(sender, instance, created, **kwargs):
    """Crée un événement DRAFT à la création, ou un événement transition au changement de status."""
    from .codelists import LifecycleState
    from .models import InvoiceLifecycleEvent

    try:
        if created:
            InvoiceLifecycleEvent.record(
                invoice=instance,
                state=LifecycleState.DRAFT,
                source="invoice.created",
                payload={"number": instance.number, "status": instance.status},
            )
            return

        old_status = getattr(instance, "_einvoicing_old_status", None)
        if old_status == instance.status:
            return  # rien à journaliser

        new_state = _map_invoice_status_to_lifecycle(instance.status)
        if not new_state:
            return  # status inconnu : on ne pollue pas l'audit

        InvoiceLifecycleEvent.record(
            invoice=instance,
            state=new_state,
            source="invoice.status_change",
            payload={
                "from_status": old_status,
                "to_status": instance.status,
                "number": instance.number,
            },
        )
    except Exception:  # noqa: BLE001 — l'audit ne doit jamais casser l'écriture métier
        logger.exception("einvoicing: échec enregistrement lifecycle event pour Invoice id=%s", instance.pk)
