
from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Invoice

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Invoice)
def notify_invoice_created(sender, instance: Invoice, created: bool, **kwargs) -> None:
    """Notification asynchrone lors de la création d'une facture."""
    if not created:
        return
    
    try:
        from core.tasks import async_notify_invoice_created
        async_notify_invoice_created(instance.pk)
    except Exception as e:
        logger.error(f"Erreur dispatch notification facture : {e}")
