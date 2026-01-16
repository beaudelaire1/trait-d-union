
from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.template.loader import render_to_string

from .models import Invoice

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Invoice)
def notify_invoice_created(sender, instance: Invoice, created: bool, **kwargs) -> None:
    """Notification HTML lors de la création d'une facture."""
    if not created:
        return
    
    recipient = getattr(settings, "TASK_NOTIFICATION_EMAIL", getattr(settings, "ADMIN_EMAIL", ""))
    if not recipient:
        return
    
    num = instance.number or instance.pk
    total = getattr(instance, "total_ttc", None) or getattr(instance, "total", "N/A")
    subject = f"[Trait d'Union Studio] Facture #{num} générée"
    
    # Utiliser le template HTML générique
    html_body = render_to_string('emails/notification_generic.html', {
        'headline': 'Nouvelle facture générée',
        'intro': f'Une nouvelle facture a été créée dans le système.',
        'rows': [
            {'label': 'Numéro', 'value': str(num)},
            {'label': 'Total TTC', 'value': f'{total} €'},
        ],
    })
    
    # Envoyer via Brevo ou fallback Django
    try:
        from core.services.email_backends import send_transactional_email, brevo_service
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'contact@traitdunion.it')
        from_name = getattr(settings, 'DEFAULT_FROM_NAME', "Trait d'Union Studio")
        
        if brevo_service.is_configured():
            result = send_transactional_email(
                to_email=recipient,
                subject=subject,
                html_content=html_body,
                from_email=from_email,
                from_name=from_name,
                tags=['facture', 'notification', 'admin']
            )
            if not result.get('success'):
                logger.warning(f"Échec notification facture {num}: {result.get('error')}")
        else:
            # Fallback Django EmailMessage
            from django.core.mail import EmailMessage
            email = EmailMessage(subject=subject, body=html_body, from_email=from_email, to=[recipient])
            email.content_subtype = 'html'
            email.send(fail_silently=True)
            
    except Exception as e:
        logger.error(f"Erreur notification facture {num}: {e}")
