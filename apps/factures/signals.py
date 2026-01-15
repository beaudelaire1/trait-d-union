
from __future__ import annotations
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from .models import Invoice


@receiver(post_save, sender=Invoice)
def notify_invoice_created(sender, instance: Invoice, created: bool, **kwargs) -> None:
    """Notification HTML lors de la création d'une facture."""
    if not created:
        return
    
    recipient = getattr(settings, "TASK_NOTIFICATION_EMAIL", getattr(settings, "DEFAULT_FROM_EMAIL", ""))
    if not recipient:
        return
    
    num = instance.number or instance.pk
    total = getattr(instance, "total_ttc", None) or getattr(instance, "total", "N/A")
    subject = f"[Nettoyage Express] Facture #{num} générée"
    
    # Utiliser le template HTML générique
    html_body = render_to_string('emails/notification_generic.html', {
        'headline': 'Nouvelle facture générée',
        'intro': f'Une nouvelle facture a été créée dans le système.',
        'rows': [
            {'label': 'Numéro', 'value': str(num)},
            {'label': 'Total TTC', 'value': f'{total} €'},
        ],
    })
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@nettoyageexpresse.fr')
    email = EmailMessage(subject=subject, body=html_body, from_email=from_email, to=[recipient])
    email.content_subtype = 'html'
    
    try:
        email.send(fail_silently=True)
    except Exception:
        pass
