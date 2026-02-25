from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from allauth.account.signals import user_logged_in as allauth_user_logged_in
import logging

from .models import Quote
from core.services.notification_service import notification_service
from apps.devis.application.validate_quote_usecase import provision_client_account

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Quote)
def auto_provision_client_on_quote_validated(sender, instance: Quote, update_fields, **kwargs):
    """Signal TUS FLOW : quand un devis passe en VALIDATED, créer le compte client.
    
    Trigger : Quote.status change to VALIDATED
    Effet : créer User + ClientProfile + envoyer email accueil + forcer changement pwd
    """
    # Skip during tests
    if getattr(settings, 'TESTING', False):
        return
    
    # Vérifier que le changement concerne le statut
    if update_fields is None or 'status' in update_fields:
        # Vérifier le nouveau statut
        if instance.status == Quote.QuoteStatus.VALIDATED:
            try:
                result = provision_client_account(instance)
                
                if result.is_new:
                    logger.info(
                        f"Auto-onboarding client : {result.user.email}",
                        extra={'quote_pk': instance.pk, 'user_pk': result.user.pk}
                    )
                else:
                    logger.info(
                        f"Compte client existant, skip création : {result.user.email}",
                        extra={'quote_pk': instance.pk}
                    )
                
            except Exception as e:
                # Log l'erreur mais ne bloque pas la validation du devis
                logger.exception(
                    f"Erreur auto-onboarding devis {instance.number}: {e}",
                    extra={'quote_pk': instance.pk}
                )


@receiver(post_save, sender=Quote)
def handle_quote_validation(sender, instance, created, **kwargs):
    """
    Handle automatic client account creation when quote is validated (accepted).
    DEPRECATED : remplacé par auto_provision_client_on_quote_validated (VALIDATED status)
    """
    # Skip during tests unless explicitly enabled
    if getattr(settings, 'TESTING', True):
        return
        
    # Only trigger on status change to ACCEPTED, not on creation
    if created:
        return
        
    # Check if quote was just accepted (old behavior, kept for backward compat)
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

    # Use async dispatch
    try:
        from core.tasks import async_send_quote_email
        if not instance.pdf:
            instance.generate_pdf(attach=True)
        async_send_quote_email(instance.pk)
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi automatique du devis {instance.pk}: {e}")


@receiver(allauth_user_logged_in)
def force_password_change_on_login(sender, request, user, **kwargs):
    """Signal : à la première connexion, forcer changement de mot de passe.
    
    Utilise le champ persistant `must_change_password` sur ClientProfile.
    Vérifie UNIQUEMENT si le flag est True (mis lors de la création du compte).
    Le flag est retiré après le changement effectif de mot de passe (voir middleware).
    """
    try:
        client_profile = user.client_profile
        
        if client_profile.must_change_password:
            request.session['must_change_password'] = True
            request.session['must_change_password_reason'] = 'first_login'
            
            logger.info(
                f"Première connexion client, changement de mot de passe requis : {user.email}",
                extra={'user_pk': user.pk}
            )
    except (AttributeError, ClientProfile.DoesNotExist):
        # Pas un profil client
        pass

