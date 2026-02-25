from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from allauth.account.signals import user_logged_in as allauth_user_logged_in
import logging

from .models import Quote
from apps.devis.application.validate_quote_usecase import provision_client_account

logger = logging.getLogger(__name__)


# Statuts déclenchant l'onboarding client automatique.
# ACCEPTED = validation par le client (code OTP / e-signature)
# VALIDATED = validation administrative (back-office)
_ONBOARDING_STATUSES = frozenset({
    Quote.QuoteStatus.ACCEPTED,
    Quote.QuoteStatus.VALIDATED,
})


@receiver(post_save, sender=Quote)
def auto_provision_client_on_quote_accepted_or_validated(
    sender, instance: Quote, update_fields, **kwargs
):
    """Signal TUS FLOW : quand un devis passe en ACCEPTED ou VALIDATED,
    créer automatiquement le compte client.

    Trigger :
        - ACCEPTED : le client a validé via code OTP (e-signature)
        - VALIDATED : un admin a validé depuis le back-office

    Effet : créer User + ClientProfile + envoyer email accueil + forcer changement pwd
    """
    if getattr(settings, 'TESTING', False):
        return

    if update_fields is not None and 'status' not in update_fields:
        return

    if instance.status not in _ONBOARDING_STATUSES:
        return

    try:
        result = provision_client_account(instance)

        if result.is_new:
            logger.info(
                "Auto-onboarding client : %s (devis %s, status=%s)",
                result.user.email,
                instance.number,
                instance.status,
                extra={'quote_pk': instance.pk, 'user_pk': result.user.pk},
            )
        else:
            logger.info(
                "Compte client existant, skip création : %s (devis %s)",
                result.user.email,
                instance.number,
                extra={'quote_pk': instance.pk},
            )
    except Exception:
        logger.exception(
            "Erreur auto-onboarding devis %s (status=%s)",
            instance.number,
            instance.status,
            extra={'quote_pk': instance.pk},
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
    except (AttributeError, Exception) as exc:
        # Pas un profil client
        pass

