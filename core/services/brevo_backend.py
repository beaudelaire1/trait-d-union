"""
Django Email Backend qui envoie via l'API REST Brevo.

Remplace le SMTP backend : tous les EmailMessage / EmailMultiAlternatives
sont automatiquement envoyés via l'API transactionnelle Brevo.

Usage dans settings :
    EMAIL_BACKEND = 'core.services.brevo_backend.BrevoEmailBackend'
"""
from __future__ import annotations

import base64
import logging
from typing import Optional

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class BrevoEmailBackend(BaseEmailBackend):
    """Django email backend qui route vers l'API REST Brevo."""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'BREVO_API_KEY', '')
        self._api_instance = None

    @property
    def api_instance(self):
        if self._api_instance is None:
            import sib_api_v3_sdk

            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = self.api_key
            self._api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )
        return self._api_instance

    def send_messages(self, email_messages) -> int:
        """Envoie une liste d'EmailMessage via l'API Brevo."""
        if not self.api_key:
            logger.warning("BREVO_API_KEY non configuré — emails non envoyés")
            return 0

        sent = 0
        for message in email_messages:
            try:
                if self._send_one(message):
                    sent += 1
            except Exception as e:
                logger.error("Erreur envoi Brevo pour '%s': %s", message.subject, e)
                if not self.fail_silently:
                    raise
        return sent

    def _send_one(self, message) -> bool:
        """Envoie un seul EmailMessage via Brevo."""
        import sib_api_v3_sdk

        # Récupérer le contenu HTML
        html_content = None
        text_content = message.body

        # Si c'est un EmailMultiAlternatives, chercher le contenu HTML
        if hasattr(message, 'alternatives'):
            for content, mimetype in message.alternatives:
                if mimetype == 'text/html':
                    html_content = content
                    break

        # Si content_subtype est html, le body est du HTML
        if getattr(message, 'content_subtype', 'plain') == 'html':
            html_content = message.body

        # Fallback : envelopper le texte brut en HTML minimal
        if not html_content:
            html_content = f"<pre style='font-family:sans-serif;white-space:pre-wrap;'>{text_content}</pre>"

        # Destinataires
        to_list = [
            sib_api_v3_sdk.SendSmtpEmailTo(email=addr)
            for addr in message.to
        ]

        # Expéditeur
        from_email = message.from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', '')
        from_name = getattr(settings, 'DEFAULT_FROM_NAME', "Trait d'Union Studio")

        # Construire le payload
        smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to_list,
            sender=sib_api_v3_sdk.SendSmtpEmailSender(
                email=from_email,
                name=from_name,
            ),
            subject=message.subject,
            html_content=html_content,
        )

        # BCC
        if message.bcc:
            smtp_email.bcc = [
                sib_api_v3_sdk.SendSmtpEmailBcc(email=addr)
                for addr in message.bcc
            ]

        # CC
        if message.cc:
            smtp_email.cc = [
                sib_api_v3_sdk.SendSmtpEmailCc(email=addr)
                for addr in message.cc
            ]

        # Reply-To
        if message.reply_to:
            smtp_email.reply_to = sib_api_v3_sdk.SendSmtpEmailReplyTo(
                email=message.reply_to[0]
            )

        # Pièces jointes
        if message.attachments:
            brevo_attachments = []
            for attachment in message.attachments:
                if isinstance(attachment, tuple):
                    filename, content, mimetype = attachment
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    brevo_attachments.append(
                        sib_api_v3_sdk.SendSmtpEmailAttachment(
                            name=filename or 'attachment',
                            content=base64.b64encode(content).decode('utf-8'),
                        )
                    )
            if brevo_attachments:
                smtp_email.attachment = brevo_attachments

        # Envoi
        response = self.api_instance.send_transac_email(smtp_email)
        logger.info(
            "Email envoyé via Brevo API: '%s' → %s (ID: %s)",
            message.subject,
            ', '.join(message.to),
            response.message_id,
        )
        return True
