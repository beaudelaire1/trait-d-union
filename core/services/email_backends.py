"""
Service d'envoi d'emails via Brevo (ex-Sendinblue).

- API REST Brevo pour les emails transactionnels
- Fallback Django pour les envois simples
- Pièces jointes et tags de suivi
- Pré-en-têtes utiles pour que les aperçus Gmail/Outlook donnent du contexte
"""
from __future__ import annotations

import base64
import logging
from html import escape
from typing import Optional

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


def _clean_display_name(value: Optional[str]) -> str:
    """Nettoie les échappements accidentels dans les noms affichés des emails."""
    cleaned = str(value or '').strip()
    cleaned = cleaned.replace("\\'", "'").replace('\\’', '’').replace('\\‘', '‘')

    # Le nom de marque doit toujours être affiché sans caractère d'échappement.
    normalized_brand = cleaned.replace('’', "'").replace('‘', "'")
    if normalized_brand == "Trait d'Union Studio":
        return "Trait d'Union Studio"

    return cleaned


def _transactional_preheader(subject: str, tags: Optional[list[str]] = None) -> str:
    """Retourne un aperçu court et non sensible selon le type d'email.

    Le pré-en-tête est volontairement neutre pour les emails de sécurité :
    aucun code OTP, mot de passe temporaire ou donnée confidentielle n'y figure.
    """
    tagset = set(tags or [])

    if 'otp' in tagset or 'validation' in tagset:
        return "Validation sécurisée de votre devis : code valable 30 minutes. Ne le communiquez à personne."
    if 'welcome' in tagset:
        return "Votre espace client est prêt : identifiants temporaires, lien de connexion et première étape."
    if 'password_changed' in tagset or 'security' in tagset:
        return "Confirmation de sécurité : votre mot de passe a été modifié. Contactez-nous si ce changement ne vient pas de vous."
    if 'lead' in tagset or 'contact' in tagset:
        return "Votre demande a bien été reçue : récapitulatif et prochaines étapes dans cet email."
    if 'devis' in tagset or 'quote' in tagset:
        return "Votre devis est disponible : consultez le PDF et les étapes de validation en ligne."
    if 'payment' in tagset:
        return "Confirmation de paiement : retrouvez dans cet email la référence et les informations utiles."

    return subject


def _inject_preheader(html_content: str, subject: str, tags: Optional[list[str]] = None) -> str:
    """Ajoute un pré-en-tête invisible au début du HTML si nécessaire."""
    if not html_content:
        return html_content
    if 'data-tus-preheader=' in html_content:
        return html_content

    preview = escape(_transactional_preheader(subject, tags))
    preheader = (
        '<div data-tus-preheader="1" '
        'style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;'
        'mso-hide:all;font-size:1px;line-height:1px;">'
        f'{preview}</div>'
    )

    lower = html_content.lower()
    body_start = lower.find('<body')
    if body_start != -1:
        body_close = html_content.find('>', body_start)
        if body_close != -1:
            return html_content[:body_close + 1] + preheader + html_content[body_close + 1:]
    return preheader + html_content


class BrevoEmailService:
    """Service d'envoi d'emails via l'API Brevo."""

    def __init__(self):
        self.api_key = getattr(settings, 'BREVO_API_KEY', None)
        self.default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'contact@traitdunion.studio')
        self.default_from_name = _clean_display_name(
            getattr(settings, 'DEFAULT_FROM_NAME', "Trait d'Union Studio")
        )
        self._api_instance = None

    @property
    def api_instance(self):
        """Lazy loading de l'instance API Brevo."""
        if self._api_instance is None:
            try:
                import sib_api_v3_sdk
                from sib_api_v3_sdk.rest import ApiException  # noqa: F401

                configuration = sib_api_v3_sdk.Configuration()
                configuration.api_key['api-key'] = self.api_key
                self._api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                    sib_api_v3_sdk.ApiClient(configuration)
                )
            except ImportError:
                logger.error("Le package sib-api-v3-sdk n'est pas installé")
                raise
        return self._api_instance

    def is_configured(self) -> bool:
        """Vérifie si Brevo est correctement configuré."""
        return bool(self.api_key)

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        *,
        to_name: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[list[dict]] = None,
        tags: Optional[list[str]] = None,
    ) -> dict:
        """Envoie un email transactionnel via Brevo."""
        if not self.is_configured():
            logger.warning("Brevo non configuré, email non envoyé: %s", subject)
            if settings.DEBUG:
                logger.debug("[DEV EMAIL] To: %s | Subject: %s", to_email, subject)
                return {'success': True, 'message_id': 'dev-mode', 'fallback': True}
            return {'success': False, 'error': 'Brevo non configuré'}

        try:
            import sib_api_v3_sdk

            html_content = _inject_preheader(html_content, subject, tags)
            sender_name = _clean_display_name(from_name or self.default_from_name)

            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[sib_api_v3_sdk.SendSmtpEmailTo(
                    email=to_email,
                    name=to_name or to_email.split('@')[0]
                )],
                sender=sib_api_v3_sdk.SendSmtpEmailSender(
                    email=from_email or self.default_from_email,
                    name=sender_name
                ),
                subject=subject,
                html_content=html_content,
            )

            if reply_to:
                send_smtp_email.reply_to = sib_api_v3_sdk.SendSmtpEmailReplyTo(email=reply_to)

            if attachments:
                brevo_attachments = []
                for att in attachments:
                    content = att.get('content', b'')
                    if isinstance(content, bytes):
                        content = base64.b64encode(content).decode('utf-8')
                    brevo_attachments.append(
                        sib_api_v3_sdk.SendSmtpEmailAttachment(
                            name=att.get('name', 'attachment'),
                            content=content
                        )
                    )
                send_smtp_email.attachment = brevo_attachments

            if tags:
                send_smtp_email.tags = tags

            api_response = self.api_instance.send_transac_email(send_smtp_email)
            logger.info(
                "Email envoyé via Brevo: %s -> %s (ID: %s)",
                subject, to_email, api_response.message_id
            )
            return {'success': True, 'message_id': api_response.message_id}

        except Exception as e:
            error_msg = str(e)
            if 'ApiException' in type(e).__name__ or hasattr(e, 'status'):
                logger.error("Erreur API Brevo: %s", e)
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': getattr(e, 'status', None)
                }
            logger.error("Erreur lors de l'envoi via Brevo: %s", e)
            return {'success': False, 'error': error_msg}

    def send_email_with_template(
        self,
        to_email: str,
        template_id: int,
        params: dict,
        *,
        to_name: Optional[str] = None,
        attachments: Optional[list[dict]] = None,
    ) -> dict:
        """Envoie un email utilisant un template Brevo."""
        if not self.is_configured():
            logger.warning("Brevo non configuré, email template non envoyé")
            return {'success': False, 'error': 'Brevo non configuré'}

        try:
            import sib_api_v3_sdk
            from sib_api_v3_sdk.rest import ApiException

            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[sib_api_v3_sdk.SendSmtpEmailTo(
                    email=to_email,
                    name=to_name or to_email.split('@')[0]
                )],
                template_id=template_id,
                params=params,
            )

            if attachments:
                brevo_attachments = []
                for att in attachments:
                    content = att.get('content', b'')
                    if isinstance(content, bytes):
                        content = base64.b64encode(content).decode('utf-8')
                    brevo_attachments.append(
                        sib_api_v3_sdk.SendSmtpEmailAttachment(
                            name=att.get('name', 'attachment'),
                            content=content
                        )
                    )
                send_smtp_email.attachment = brevo_attachments

            api_response = self.api_instance.send_transac_email(send_smtp_email)
            logger.info(
                "Email template envoyé via Brevo: template=%d -> %s (ID: %s)",
                template_id, to_email, api_response.message_id
            )
            return {'success': True, 'message_id': api_response.message_id}

        except ApiException as e:
            logger.error("Erreur API Brevo (template): %s", e)
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error("Erreur lors de l'envoi template via Brevo: %s", e)
            return {'success': False, 'error': str(e)}


brevo_service = BrevoEmailService()


def send_transactional_email(
    to_email: str,
    subject: str,
    html_content: str,
    **kwargs
) -> dict:
    """Fonction utilitaire principale pour envoyer un email transactionnel."""
    return brevo_service.send_email(to_email, subject, html_content, **kwargs)


def send_simple_email(
    to_email: str,
    subject: str,
    text_body: str,
    *,
    html_body: Optional[str] = None,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    attachments: Optional[list[dict]] = None,
    bcc: Optional[list[str]] = None,
) -> bool:
    """Envoie un email simple via Brevo ou fallback Django."""
    if brevo_service.is_configured():
        content = html_body or f"<pre style='font-family: sans-serif;'>{escape(text_body)}</pre>"

        result = brevo_service.send_email(
            to_email=to_email,
            subject=subject,
            html_content=content,
            from_email=from_email,
            from_name=from_name,
            attachments=attachments,
        )

        if bcc and result.get('success'):
            for bcc_email in bcc:
                brevo_service.send_email(
                    to_email=bcc_email,
                    subject=subject,
                    html_content=content,
                    from_email=from_email,
                    from_name=from_name,
                )

        return result.get('success', False)

    try:
        _from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'contact@traitdunion.studio')
        email = EmailMessage(
            subject=subject,
            body=html_body or text_body,
            from_email=_from_email,
            to=[to_email],
            bcc=bcc,
        )

        if html_body:
            email.content_subtype = 'html'

        if attachments:
            for att in attachments:
                email.attach(
                    att.get('name', 'attachment'),
                    att.get('content', b''),
                    att.get('mime_type', 'application/octet-stream')
                )

        return email.send(fail_silently=True) > 0

    except Exception as e:
        logger.error("Erreur envoi email via Django: %s", e)
        return False
