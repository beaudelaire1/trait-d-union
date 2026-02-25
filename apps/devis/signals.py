from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from allauth.account.signals import user_logged_in as allauth_user_logged_in
import logging

from .models import Quote
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
def send_quote_with_pdf(sender, instance, created, **kwargs):
    """
    Envoi automatique du devis au client par e-mail avec le PDF joint.
    """
    # Skip email sending during tests
    if getattr(settings, 'TESTING', False):
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


from django.contrib.auth.signals import user_logged_in as django_user_logged_in

@receiver(allauth_user_logged_in)
@receiver(django_user_logged_in)
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

