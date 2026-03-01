"""Signal handlers for automatic client notifications."""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.devis.models import Quote
from apps.factures.models import Invoice
from apps.clients.models import ClientNotification, ClientProfile

logger = logging.getLogger(__name__)


def _resolve_profile(email: str, client_obj=None):
    """Résout un ClientProfile depuis un Client (FK) ou un email (fallback).

    🛡️ SECURITY: Prefer FK-based lookup (linked_profile) over email matching.
    """
    # 🛡️ BANK-GRADE: Only use FK-based lookup. No email fallback (IDOR risk).
    if client_obj and hasattr(client_obj, 'linked_profile') and client_obj.linked_profile_id:
        return client_obj.linked_profile
    return None


@receiver(post_save, sender=Quote)
def notify_quote_created(sender, instance, created, **kwargs):
    """Send notification when a new quote is created."""
    if not (created and instance.status == 'sent'):
        return
    try:
        profile = _resolve_profile(instance.client.email, client_obj=instance.client)
        if profile:
            ClientNotification.objects.create(
                client=profile,
                notification_type='quote',
                title='Nouveau devis disponible',
                message=f'Un nouveau devis #{instance.number} a été créé pour vous.',
                related_url=f'/ecosysteme-tus/devis/{instance.pk}/'
            )
    except Exception:
        logger.exception("Erreur notification création devis %s", instance.pk)


@receiver(post_save, sender=Quote)
def notify_quote_accepted(sender, instance, created, **kwargs):
    """Send notification when a quote is accepted (only once)."""
    if created:
        return
    if not (instance.status == 'accepted' and instance.signed_at):
        return
    try:
        profile = _resolve_profile(instance.client.email, client_obj=instance.client)
        if profile and not ClientNotification.objects.filter(
            client=profile, notification_type='quote',
            title='Devis accepté', related_url=f'/ecosysteme-tus/devis/{instance.pk}/'
        ).exists():
            ClientNotification.objects.create(
                client=profile,
                notification_type='quote',
                title='Devis accepté',
                message=f'Votre devis #{instance.number} a été accepté. Nous commençons votre projet !',
                related_url=f'/ecosysteme-tus/devis/{instance.pk}/'
            )
    except Exception:
        logger.exception("Erreur notification acceptation devis %s", instance.pk)


def _resolve_invoice_client(invoice):
    """Retourne le client résolu d'une facture."""
    return invoice.client or (invoice.quote.client if invoice.quote else None)


@receiver(post_save, sender=Invoice)
def notify_invoice_created(sender, instance, created, **kwargs):
    """Send notification when a new invoice is created."""
    if not (created and instance.status == 'sent'):
        return
    try:
        client_obj = _resolve_invoice_client(instance)
        if not client_obj:
            return
        profile = _resolve_profile(client_obj.email, client_obj=client_obj)
        if profile:
            ClientNotification.objects.create(
                client=profile,
                notification_type='invoice',
                title='Nouvelle facture disponible',
                message=f'La facture #{instance.number} est disponible pour un montant de {instance.total_ttc}€.',
                related_url=f'/ecosysteme-tus/factures/{instance.pk}/'
            )
    except Exception:
        logger.exception("Erreur notification création facture %s", instance.pk)


@receiver(post_save, sender=Invoice)
def notify_invoice_paid(sender, instance, created, **kwargs):
    """Send notification when an invoice is paid (only once)."""
    if created:
        return
    if not (instance.status == 'paid' and instance.paid_at):
        return
    try:
        client_obj = _resolve_invoice_client(instance)
        if not client_obj:
            return
        profile = _resolve_profile(client_obj.email, client_obj=client_obj)
        if profile and not ClientNotification.objects.filter(
            client=profile, notification_type='invoice',
            title='Paiement reçu', related_url=f'/ecosysteme-tus/factures/{instance.pk}/'
        ).exists():
            ClientNotification.objects.create(
                client=profile,
                notification_type='invoice',
                title='Paiement reçu',
                message=f'Votre paiement pour la facture #{instance.number} a été reçu. Merci !',
                related_url=f'/ecosysteme-tus/factures/{instance.pk}/'
            )
    except Exception:
        logger.exception("Erreur notification paiement facture %s", instance.pk)
