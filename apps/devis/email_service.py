"""
Service d'envoi d'emails pour les devis.

Ce module gère l'envoi des emails transactionnels liés aux devis :
- Envoi du devis au client (avec PDF en pièce jointe)
- Envoi du code OTP pour la validation

Utilise Brevo (ex-Sendinblue) si configuré, sinon fallback Django EmailMessage.
"""
from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)


def _get_email_backend() -> str:
    """
    Retourne le backend d'email approprié.
    
    Utilise Brevo si configuré, sinon fallback sur Django EmailMessage.
    """
    try:
        from core.services.email_backends import brevo_service
        if brevo_service.is_configured():
            return 'brevo'
    except ImportError:
        pass
    return 'django'


def _base_url(request=None) -> str:
    """Return the base URL for absolute links in emails."""
    if request is not None:
        try:
            return request.build_absolute_uri('/').rstrip('/')
        except Exception:
            pass
    return str(getattr(settings, 'SITE_URL', 'http://localhost:8000')).rstrip('/')


def _send_via_brevo(
    recipient: str,
    subject: str,
    html_body: str,
    *,
    recipient_name: Optional[str] = None,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    attachments: Optional[list[dict]] = None,
    tags: Optional[list[str]] = None,
) -> None:
    """Envoie un email via Brevo."""
    from core.services.email_backends import send_transactional_email
    
    result = send_transactional_email(
        to_email=recipient,
        subject=subject,
        html_content=html_body,
        to_name=recipient_name,
        from_email=from_email,
        from_name=from_name,
        attachments=attachments,
        tags=tags
    )
    
    if not result.get('success'):
        raise Exception(f"Échec envoi Brevo: {result.get('error')}")
    
    logger.info(f"Email envoyé via Brevo à {recipient} (ID: {result.get('message_id')})")


def _send_via_django(
    recipient: str,
    subject: str,
    html_body: str,
    *,
    from_email: Optional[str] = None,
    attachments: Optional[list[dict]] = None,
) -> None:
    """Envoie un email via Django EmailMessage (fallback)."""
    email = EmailMessage(
        subject=subject,
        body=html_body,
        from_email=from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'contact@traitdunion.it'),
        to=[recipient]
    )
    email.content_subtype = 'html'
    
    if attachments:
        for att in attachments:
            email.attach(att['name'], att['content'], att.get('mime_type', 'application/pdf'))
    
    email.send(fail_silently=False)
    logger.info(f"Email envoyé via Django à {recipient}")


def send_quote_email(quote, request=None, *, to_email: Optional[str] = None) -> None:
    """
    Envoie le devis au client avec le PDF en pièce jointe.

    Uses templates/emails/modele_quote.html (provided by the user).
    
    Args:
        quote: Instance du modèle Quote
        request: HttpRequest pour construire les URLs absolues
        to_email: Email destinataire (optionnel, utilise quote.client.email sinon)
    """
    # Ensure totals are up-to-date
    try:
        quote.compute_totals()
    except Exception:
        pass

    # Ensure we have a stable public token for links (backfill if legacy data)
    if not getattr(quote, 'public_token', None):
        try:
            quote.save(update_fields=["public_token"])
        except Exception:
            try:
                quote.save()
            except Exception:
                pass

    base = _base_url(request)
    # Public PDF link uses Quote.public_token (stable).
    # Validation link must point to the START step with the *public_token*.
    # IMPORTANT: Per requirement, the OTP code MUST NOT appear in the quote email.
    # It is sent in a separate email when the client clicks the validation link.
    pdf_url = f"{base}{reverse('devis:quote_public_pdf', kwargs={'token': quote.public_token})}"
    validation_url = f"{base}{reverse('devis:quote_validate_start', kwargs={'token': quote.public_token})}"

    client = getattr(quote, 'client', None)
    client_name = getattr(client, 'full_name', '') if client is not None else ''
    recipient = to_email or (getattr(client, 'email', None) if client is not None else None)
    if not recipient:
        logger.warning(f"Aucun destinataire pour le devis {quote.number}")
        return

    branding = getattr(settings, 'INVOICE_BRANDING', {})
    company_name = branding.get('name', "Trait d'Union Studio")
    subject = f"Votre devis {quote.number} — {company_name}"

    # HTML ONLY: aucune notification en texte (exigence projet)
    html_body = render_to_string(
        'emails/modele_quote.html',
        {
            'quote': quote,
            'client_name': client_name or 'Bonjour',
            'company_name': company_name,
            'pdf_url': pdf_url,
            'validation_url': validation_url,
        },
    )

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'contact@traitdunion.it'
    from_name = getattr(settings, 'DEFAULT_FROM_NAME', "Trait d'Union Studio")
    
    # Email admin pour copie (TASK_NOTIFICATION_EMAIL ou ADMIN_EMAIL)
    admin_email = (
        getattr(settings, 'TASK_NOTIFICATION_EMAIL', None) or 
        getattr(settings, 'ADMIN_EMAIL', None) or 
        'contact@traitdunion.it'
    )
    
    # Générer le PDF pour la pièce jointe
    attachments = []
    try:
        pdf_bytes = quote.generate_pdf(attach=False)
        if pdf_bytes:
            attachments.append({
                'name': f"{quote.number}.pdf",
                'content': pdf_bytes,
                'mime_type': 'application/pdf'
            })
    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF pour le devis {quote.number}: {e}")
        # Continue without PDF attachment

    # Utiliser Brevo si configuré, sinon fallback Django
    backend = _get_email_backend()
    
    try:
        if backend == 'brevo':
            # Envoi au client
            _send_via_brevo(
                recipient=recipient,
                subject=subject,
                html_body=html_body,
                recipient_name=client_name or None,
                from_email=from_email,
                from_name=from_name,
                attachments=attachments if attachments else None,
                tags=['devis', 'quote', f'quote-{quote.number}']
            )
            
            # Copie à l'admin si différent du client
            if admin_email and admin_email != recipient:
                try:
                    _send_via_brevo(
                        recipient=admin_email,
                        subject=f"[Copie] {subject}",
                        html_body=html_body,
                        from_email=from_email,
                        from_name=from_name,
                        attachments=attachments if attachments else None,
                        tags=['devis', 'quote', 'admin-copy']
                    )
                    logger.info(f"Copie du devis {quote.number} envoyée à l'admin {admin_email}")
                except Exception as copy_err:
                    logger.warning(f"Échec envoi copie admin pour devis {quote.number}: {copy_err}")
        else:
            _send_via_django(
                recipient=recipient,
                subject=subject,
                html_body=html_body,
                from_email=from_email,
                attachments=attachments if attachments else None,
            )
        
        logger.info(f"Devis {quote.number} envoyé à {recipient} via {backend}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du devis {quote.number}: {e}")
        raise


def send_quote_validation_code(quote, validation, request=None, *, to_email: Optional[str] = None) -> None:
    """
    Envoie le code OTP pour la validation du devis (étape 1 du 2FA).
    
    Args:
        quote: Instance du modèle Quote
        validation: Instance QuoteValidation avec le code OTP
        request: HttpRequest pour construire les URLs absolues
        to_email: Email destinataire (optionnel)
    """
    client = getattr(quote, 'client', None)
    recipient = to_email or (getattr(client, 'email', None) if client is not None else None)
    if not recipient:
        logger.warning(f"Aucun destinataire pour le code OTP du devis {quote.number}")
        return

    base = _base_url(request)
    code_url = f"{base}{reverse('devis:quote_validate_code', kwargs={'token': validation.token})}"

    subject = f"Code de confirmation pour valider le devis {quote.number}"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'contact@traitdunion.it'
    from_name = getattr(settings, 'DEFAULT_FROM_NAME', "Trait d'Union Studio")
    client_name = getattr(client, 'full_name', '') if client else ''

    # Le template générique attend : headline/intro + action_url/action_label
    html_body = render_to_string(
        'emails/notification_generic.html',
        {
            'headline': 'Validation du devis — Code de confirmation',
            'intro': (
                f"Bonjour {client_name or ''},\n\n"
                f"Votre code de confirmation pour valider le devis {quote.number} est : {validation.code}\n\n"
                f"Ce code expire dans 15 minutes."
            ),
            'rows': [
                {'label': 'Devis', 'value': quote.number},
                {'label': 'Code', 'value': validation.code},
            ],
            'action_url': code_url,
            'action_label': 'Saisir le code',
        },
    )

    # Utiliser Brevo si configuré, sinon fallback Django
    backend = _get_email_backend()
    
    try:
        if backend == 'brevo':
            _send_via_brevo(
                recipient=recipient,
                subject=subject,
                html_body=html_body,
                recipient_name=client_name or None,
                from_email=from_email,
                from_name=from_name,
                tags=['otp', 'validation', f'quote-{quote.number}']
            )
        else:
            _send_via_django(
                recipient=recipient,
                subject=subject,
                html_body=html_body,
                from_email=from_email,
            )
        
        logger.info(f"Code OTP envoyé pour le devis {quote.number} à {recipient} via {backend}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du code OTP pour le devis {quote.number}: {e}")
        raise
