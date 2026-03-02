"""
Services de gestion des comptes clients — Écosystème TUS.

Fonctions utilitaires pour créer, provisionner et gérer les comptes
d'accès au portail client, indépendamment d'un devis.
"""
import secrets
import logging
from dataclasses import dataclass
from typing import Optional

from django.contrib.auth.models import User
from django.db import transaction
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from .models import ClientProfile

logger = logging.getLogger(__name__)


class ClientAccountError(Exception):
    """Erreur lors de la création d'un compte client."""
    pass


@dataclass
class ClientAccountResult:
    """Résultat de la création d'un compte client."""
    user: User
    client_profile: ClientProfile
    is_new: bool
    temporary_password: Optional[str] = None


def create_client_account(
    email: str,
    full_name: str = '',
    company_name: str = '',
    phone: str = '',
    address: str = '',
    *,
    send_email: bool = True,
) -> ClientAccountResult:
    """Crée un compte client (User + ClientProfile) avec mot de passe temporaire.

    Utilisable depuis :
    - L'admin devis (action sur contacts)
    - L'admin clients (création manuelle)
    - La validation de devis (use case existant)
    - Tout autre point d'entrée

    Si le User existe déjà (même email), on récupère le compte existant
    sans recréer ni renvoyer de mot de passe.

    Args:
        email: Email du client (obligatoire)
        full_name: Nom complet du client
        company_name: Nom de la société
        phone: Numéro de téléphone
        address: Adresse postale
        send_email: Envoyer l'email de bienvenue (défaut: True)

    Returns:
        ClientAccountResult avec le User, ClientProfile, et mot de passe temporaire

    Raises:
        ClientAccountError si email invalide ou erreur critique
    """
    if not email or not email.strip():
        raise ClientAccountError("L'email est obligatoire pour créer un compte client.")

    email = email.strip().lower()
    is_new = False
    temporary_password = None

    with transaction.atomic():
        try:
            user = User.objects.get(email__iexact=email)
            logger.info(f"Compte client existant : {email}")
        except User.DoesNotExist:
            is_new = True
            temporary_password = secrets.token_urlsafe(24)  # 🛡️ BANK-GRADE: 192-bit entropy

            # Username à partir de l'email
            username_base = email.split('@')[0]
            username = username_base
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{username_base}{counter}"
                counter += 1

            # Extraire prénom/nom
            first_name = ''
            last_name = ''
            if full_name:
                parts = full_name.strip().split(' ', 1)
                first_name = parts[0][:30]
                last_name = parts[1][:30] if len(parts) > 1 else ''

            user = User.objects.create_user(
                username=username,
                email=email,
                password=temporary_password,
                first_name=first_name,
                last_name=last_name,
            )
            logger.info(f"Compte client créé : {username} ({email})")

            # Allauth : marquer l'email comme vérifié (compte créé sur invitation admin)
            # Sans cela, ACCOUNT_EMAIL_VERIFICATION='mandatory' bloquerait la connexion
            try:
                from allauth.account.models import EmailAddress
                EmailAddress.objects.get_or_create(
                    user=user,
                    email=email,
                    defaults={'verified': True, 'primary': True},
                )
            except Exception as exc:
                logger.warning(f"Impossible de créer EmailAddress allauth : {exc}")

        # Créer / récupérer le ClientProfile
        client_profile, profile_created = ClientProfile.objects.get_or_create(
            user=user,
            defaults={
                'company_name': company_name or '',
                'phone': phone or '',
                'address': address or '',
                'must_change_password': is_new,
            }
        )

        if is_new:
            client_profile.must_change_password = True
            client_profile.save(update_fields=['must_change_password'])

    # Envoyer l'email de bienvenue en arrière-plan
    if is_new and send_email and temporary_password:
        try:
            from core.tasks import async_send_welcome_email
            async_send_welcome_email(user.pk, temporary_password)
        except Exception as e:
            logger.exception(f"Échec dispatch email bienvenue : {e}")

    # 🛡️ SECURITY: Auto-link any existing Client (devis) records to this profile
    try:
        from apps.devis.models import Client as DevisClient
        DevisClient.objects.filter(
            email__iexact=email,
            linked_profile__isnull=True,
        ).update(linked_profile=client_profile)
    except Exception:
        logger.exception("Échec auto-link Client → ClientProfile pour %s", email)

    return ClientAccountResult(
        user=user,
        client_profile=client_profile,
        is_new=is_new,
        temporary_password=temporary_password if is_new else None,
    )


def send_welcome_email(
    user: User,
    temporary_password: str,
    *,
    context_label: str = '',
) -> None:
    """Envoie un email de bienvenue HTML premium au client.

    Args:
        user: L'utilisateur Django créé
        temporary_password: Le mot de passe temporaire généré
        context_label: Libellé optionnel (ex: "Devis DEV-2026-042")
    """
    site_url = str(getattr(settings, 'SITE_URL', 'https://traitdunion.it')).rstrip('/')
    # Sécurité : ne jamais envoyer un lien localhost/127.0.0.1 par email
    if 'localhost' in site_url or '127.0.0.1' in site_url or '0.0.0.0' in site_url:
        logger.warning(f"SITE_URL contient localhost ({site_url!r}), fallback sur https://traitdunion.it")
        site_url = 'https://traitdunion.it'
    login_url = f"{site_url}/accounts/login/"
    first_name = user.first_name or user.username
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@traitdunion.it')

    subject = "Bienvenue chez Trait d'Union Studio — accès portail client"

    context_line = ''
    if context_label:
        context_line = f' suite à votre {context_label}'

    # Version texte
    text_content = f"""Bienvenue {first_name},

Votre espace client Trait d'Union Studio est maintenant accessible{context_line}.

Identifiants de connexion :
Email : {user.email}
Mot de passe temporaire : {temporary_password}

Connectez-vous : {login_url}

IMPORTANT : À votre première connexion, vous devrez changer ce mot de passe temporaire.

Questions ? Contactez-nous : contact@traitdunion.it

— Trait d'Union Studio"""

    # Version HTML premium
    context_html = ''
    if context_label:
        context_html = f'<br>Suite à votre <strong style="color:#0B2DFF;">{context_label}</strong>.'

    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0; padding:0; background-color:#07080A; font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#07080A; padding:40px 20px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#0D1016; border:1px solid rgba(246,247,251,0.08); border-radius:16px; overflow:hidden;">

  <!-- Header gradient -->
  <tr><td style="height:4px; background:linear-gradient(135deg,#0B2DFF 0%,#22C55E 100%);"></td></tr>

  <!-- Logo -->
  <tr><td style="padding:32px 40px 16px; text-align:center;">
    <span style="font-size:1.4rem; font-weight:700; color:#F6F7FB; letter-spacing:0.02em;">Trait d'Union Studio</span>
  </td></tr>

  <!-- Welcome -->
  <tr><td style="padding:0 40px 24px; text-align:center;">
    <h1 style="margin:0; font-size:1.6rem; font-weight:700; color:#F6F7FB;">Bienvenue {first_name} 👋</h1>
    <p style="margin:12px 0 0; font-size:0.95rem; color:rgba(246,247,251,0.7); line-height:1.6;">
      Votre espace client est maintenant accessible.{context_html}
    </p>
  </td></tr>

  <!-- Credentials box -->
  <tr><td style="padding:0 40px 24px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#111827; border:1px solid rgba(11,45,255,0.3); border-radius:12px;">
      <tr><td style="padding:24px;">
        <p style="margin:0 0 4px; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:rgba(246,247,251,0.5);">Vos identifiants</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:12px;">
          <tr>
            <td style="padding:8px 0; font-size:0.85rem; color:rgba(246,247,251,0.6); width:140px;">Email</td>
            <td style="padding:8px 0; font-size:0.95rem; color:#F6F7FB; font-weight:600;">{user.email}</td>
          </tr>
          <tr>
            <td style="padding:8px 0; font-size:0.85rem; color:rgba(246,247,251,0.6);">Mot de passe</td>
            <td style="padding:8px 0;">
              <code style="background:rgba(11,45,255,0.15); color:#4D6FFF; padding:4px 12px; border-radius:6px; font-size:0.9rem; font-weight:600;">{temporary_password}</code>
            </td>
          </tr>
        </table>
      </td></tr>
    </table>
  </td></tr>

  <!-- Warning -->
  <tr><td style="padding:0 40px 24px;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.25); border-radius:8px;">
      <tr><td style="padding:14px 18px; font-size:0.85rem; color:#FCD34D;">
        ⚠️ <strong>Important :</strong> À votre première connexion, vous devrez changer ce mot de passe temporaire.
      </td></tr>
    </table>
  </td></tr>

  <!-- CTA Button -->
  <tr><td style="padding:0 40px 32px; text-align:center;">
    <a href="{login_url}" style="display:inline-block; background:linear-gradient(135deg,#0B2DFF,#22C55E); color:#fff; text-decoration:none; padding:14px 40px; border-radius:8px; font-weight:700; font-size:0.95rem; letter-spacing:0.02em;">
      Accéder à mon espace client →
    </a>
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding:24px 40px; border-top:1px solid rgba(246,247,251,0.08); text-align:center;">
    <p style="margin:0; font-size:0.78rem; color:rgba(246,247,251,0.35);">
      Trait d'Union Studio · Guyane<br>
      Questions ? <a href="mailto:contact@traitdunion.it" style="color:#4D6FFF; text-decoration:none;">contact@traitdunion.it</a>
    </p>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    # Envoi : priorité API Brevo, fallback Django SMTP/console
    try:
        from core.services.email_backends import brevo_service
        if brevo_service.is_configured():
            brevo_service.send_email(
                to_email=user.email,
                to_name=first_name,
                subject=subject,
                html_content=html_content,
                from_email=from_email,
                from_name=getattr(settings, 'DEFAULT_FROM_NAME', "Trait d'Union Studio"),
                tags=['welcome', 'client', 'portal'],
            )
            logger.info(f"Email bienvenue envoyé via Brevo à {user.email}")
            return
    except Exception as exc:
        logger.warning(f"Brevo indisponible, fallback Django: {exc}")

    msg = EmailMultiAlternatives(subject, text_content, from_email, [user.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


def reset_password_and_notify(user: User) -> str:
    """Réinitialise le mot de passe d'un client et envoie un nouvel email.

    Utile pour :
    - Renvoyer les identifiants à un client
    - Réinitialiser un mot de passe oublié depuis l'admin

    Returns:
        Le nouveau mot de passe temporaire
    """
    new_password = secrets.token_urlsafe(24)  # 🛡️ BANK-GRADE: 192-bit entropy
    user.set_password(new_password)
    user.save(update_fields=['password'])

    # Activer le flag must_change_password
    try:
        profile = user.client_profile
        profile.must_change_password = True
        profile.save(update_fields=['must_change_password'])
    except ClientProfile.DoesNotExist:
        pass

    send_welcome_email(user, new_password, context_label='réinitialisation de mot de passe')
    return new_password
