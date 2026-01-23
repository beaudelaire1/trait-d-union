"""Signal handlers for automatic client notifications."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.devis.models import Quote
from apps.factures.models import Invoice
from apps.clients.models import ClientNotification, ClientProfile


@receiver(post_save, sender=Quote)
def notify_quote_created(sender, instance, created, **kwargs):
    """Send notification when a new quote is created."""
    if created and instance.status == 'sent':
        try:
            # Find client profile by email
            profile = ClientProfile.objects.filter(user__email=instance.client.email).first()
            if profile:
                ClientNotification.objects.create(
                    client=profile,
                    notification_type='quote',
                    title='Nouveau devis disponible',
                    message=f'Un nouveau devis #{instance.number} a été créé pour vous.',
                    link_url=f'/espace-client/devis/{instance.pk}/'
                )
        except Exception:
            pass  # Ne pas bloquer la création du devis si la notification échoue


@receiver(post_save, sender=Quote)
def notify_quote_accepted(sender, instance, **kwargs):
    """Send notification when a quote is accepted."""
    if instance.status == 'accepted' and instance.signed_at:
        try:
            profile = ClientProfile.objects.filter(user__email=instance.client.email).first()
            if profile:
                ClientNotification.objects.create(
                    client=profile,
                    notification_type='quote',
                    title='Devis accepté',
                    message=f'Votre devis #{instance.number} a été accepté. Nous commençons votre projet !',
                    link_url=f'/espace-client/devis/{instance.pk}/'
                )
        except Exception:
            pass


@receiver(post_save, sender=Invoice)
def notify_invoice_created(sender, instance, created, **kwargs):
    """Send notification when a new invoice is created."""
    if created and instance.status == 'sent':
        try:
            # Find client via quote
            if instance.quote:
                profile = ClientProfile.objects.filter(user__email=instance.quote.client.email).first()
                if profile:
                    ClientNotification.objects.create(
                        client=profile,
                        notification_type='invoice',
                        title='Nouvelle facture disponible',
                        message=f'La facture #{instance.number} est disponible pour un montant de {instance.total_ttc}€.',
                        link_url=f'/espace-client/factures/{instance.pk}/'
                    )
        except Exception:
            pass


@receiver(post_save, sender=Invoice)
def notify_invoice_paid(sender, instance, **kwargs):
    """Send notification when an invoice is paid."""
    if instance.status == 'paid' and instance.paid_at:
        try:
            if instance.quote:
                profile = ClientProfile.objects.filter(user__email=instance.quote.client.email).first()
                if profile:
                    ClientNotification.objects.create(
                        client=profile,
                        notification_type='invoice',
                        title='Paiement reçu',
                        message=f'Votre paiement pour la facture #{instance.number} a été reçu. Merci !',
                        link_url=f'/espace-client/factures/{instance.pk}/'
                    )
        except Exception:
            pass
