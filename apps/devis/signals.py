from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import Quote
from core.services.notification_service import notification_service


@receiver(post_save, sender=Quote)
def handle_quote_validation(sender, instance, created, **kwargs):
    """
    Handle automatic client account creation when quote is validated (accepted).
    """
    # Skip during tests unless explicitly enabled
    if getattr(settings, 'TESTING', True):
        return
        
    # Only trigger on status change to ACCEPTED, not on creation
    if created:
        return
        
    # Check if quote was just accepted
    if instance.status == Quote.QuoteStatus.ACCEPTED:
        from accounts.services import ClientAccountCreationService
        from core.services.email_service import EmailService
        
        try:
            # Create client account if it doesn't exist
            user, was_created = ClientAccountCreationService.create_from_quote_validation(instance)
            
            if was_created:
                # Send invitation email for new accounts
                EmailService.send_client_invitation(user, instance)
            
            # Send notification about quote validation
            notification_service.notify_quote_validation(instance)
                
        except Exception as e:
            # Log error but don't break the quote validation process
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create client account for quote {instance.pk}: {e}")


@receiver(post_save, sender=Quote)
def send_quote_with_pdf(sender, instance, created, **kwargs):
    """
    Envoi automatique du devis au client par e-mail avec le PDF joint.
    """
    # Skip email sending during tests
    if hasattr(settings, 'TESTING') or 'test' in str(settings.DATABASES['default']['NAME']):
        return
        
    if not created:
        return

    # Use the unified service method on the model
    try:
        instance.send_email()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de l'envoi automatique du devis {instance.pk}: {e}")
