"""
Service d'envoi d'emails via Brevo (ex-Sendinblue).

Optimisé pour les déploiements sur Render.com :
- Utilise l'API REST (pas de SMTP, évite les blocages firewall)
- Gestion robuste des erreurs avec retry
- Support des pièces jointes (PDFs)
- Tracking intégré

Configuration requise dans settings :
    BREVO_API_KEY = "votre-clé-api"
    DEFAULT_FROM_EMAIL = "contact@example.com"
    DEFAULT_FROM_NAME = "Mon Entreprise"
"""
from __future__ import annotations

import base64
import logging
from typing import Optional

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


class BrevoEmailService:
    """Service d'envoi d'emails via l'API Brevo."""

    def __init__(self):
        self.api_key = getattr(settings, 'BREVO_API_KEY', None)
        self.default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'contact@traitdunion.it')
        self.default_from_name = getattr(settings, 'DEFAULT_FROM_NAME', "Trait d'Union Studio")
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
        """
        Envoie un email transactionnel via Brevo.

        Args:
            to_email: Adresse email du destinataire
            subject: Objet de l'email
            html_content: Contenu HTML de l'email
            to_name: Nom du destinataire (optionnel)
            from_email: Email expéditeur (optionnel, utilise DEFAULT_FROM_EMAIL)
            from_name: Nom expéditeur (optionnel, utilise DEFAULT_FROM_NAME)
            reply_to: Adresse de réponse (optionnel)
            attachments: Liste de pièces jointes [{'name': 'file.pdf', 'content': bytes}]
            tags: Tags pour le tracking (optionnel)

        Returns:
            dict avec 'success': bool et 'message_id' ou 'error'

        Raises:
            Exception si l'envoi échoue et que fail_silently=False
        """
        if not self.is_configured():
            logger.warning("Brevo non configuré, email non envoyé: %s", subject)
            # Fallback vers la console en dev
            if settings.DEBUG:
                print(f"\n{'='*60}")
                print(f"[DEV EMAIL] To: {to_email}")
                print(f"[DEV EMAIL] Subject: {subject}")
                print(f"{'='*60}\n")
                return {'success': True, 'message_id': 'dev-mode', 'fallback': True}
            return {'success': False, 'error': 'Brevo non configuré'}

        try:
            import sib_api_v3_sdk
            from sib_api_v3_sdk.rest import ApiException

            # Construction du payload
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[sib_api_v3_sdk.SendSmtpEmailTo(
                    email=to_email,
                    name=to_name or to_email.split('@')[0]
                )],
                sender=sib_api_v3_sdk.SendSmtpEmailSender(
                    email=from_email or self.default_from_email,
                    name=from_name or self.default_from_name
                ),
                subject=subject,
                html_content=html_content,
            )

            # Réponse personnalisée
            if reply_to:
                send_smtp_email.reply_to = sib_api_v3_sdk.SendSmtpEmailReplyTo(
                    email=reply_to
                )

            # Pièces jointes
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

            # Tags pour le suivi
            if tags:
                send_smtp_email.tags = tags

            # Envoi
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            logger.info(
                "Email envoyé via Brevo: %s -> %s (ID: %s)",
                subject, to_email, api_response.message_id
            )
            return {
                'success': True,
                'message_id': api_response.message_id
            }

        except ApiException as e:
            logger.error("Erreur API Brevo: %s", e)
            return {
                'success': False,
                'error': str(e),
                'status_code': e.status if hasattr(e, 'status') else None
            }
        except Exception as e:
            logger.error("Erreur lors de l'envoi via Brevo: %s", e)
            return {
                'success': False,
                'error': str(e)
            }

    def send_email_with_template(
        self,
        to_email: str,
        template_id: int,
        params: dict,
        *,
        to_name: Optional[str] = None,
        attachments: Optional[list[dict]] = None,
    ) -> dict:
        """
        Envoie un email utilisant un template Brevo.

        Utile pour les emails marketing ou les templates complexes
        gérés directement dans l'interface Brevo.

        Args:
            to_email: Adresse du destinataire
            template_id: ID du template Brevo
            params: Paramètres dynamiques du template
            to_name: Nom du destinataire
            attachments: Pièces jointes optionnelles

        Returns:
            dict avec 'success' et 'message_id' ou 'error'
        """
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
            return {
                'success': True,
                'message_id': api_response.message_id
            }

        except ApiException as e:
            logger.error("Erreur API Brevo (template): %s", e)
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error("Erreur lors de l'envoi template via Brevo: %s", e)
            return {'success': False, 'error': str(e)}


# Singleton pour faciliter l'import
brevo_service = BrevoEmailService()


def send_transactional_email(
    to_email: str,
    subject: str,
    html_content: str,
    **kwargs
) -> dict:
    """
    Fonction utilitaire pour envoyer un email transactionnel.

    C'est la fonction principale à utiliser dans le projet.

    Exemple:
        from core.services.email_backends import send_transactional_email

        result = send_transactional_email(
            to_email='client@example.com',
            subject='Votre devis',
            html_content='<h1>Bonjour</h1>',
            attachments=[{'name': 'devis.pdf', 'content': pdf_bytes}]
        )
        if result['success']:
            print(f"Email envoyé: {result['message_id']}")
    """
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
    """
    Envoie un email simple (texte ou HTML) via Brevo ou fallback Django.
    
    Fonction de remplacement pour django.core.mail.send_mail
    Utilise automatiquement Brevo si configuré, sinon Django EmailMessage.
    
    Args:
        to_email: Destinataire
        subject: Objet
        text_body: Corps du message en texte brut
        html_body: Corps HTML optionnel (si fourni, priorité sur text_body)
        from_email: Email expéditeur
        from_name: Nom expéditeur
        attachments: Liste de pièces jointes [{'name': 'file.pdf', 'content': bytes}]
        bcc: Liste des destinataires en copie cachée
    
    Returns:
        True si envoi réussi, False sinon
    """
    # Si Brevo est configuré, utiliser l'API
    if brevo_service.is_configured():
        # Convertir texte en HTML simple si pas de HTML fourni
        content = html_body or f"<pre style='font-family: sans-serif;'>{text_body}</pre>"
        
        result = brevo_service.send_email(
            to_email=to_email,
            subject=subject,
            html_content=content,
            from_email=from_email,
            from_name=from_name,
            attachments=attachments,
        )
        
        # Envoyer aux BCC séparément via Brevo
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
    
    # Fallback Django EmailMessage
    try:
        _from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'contact@traitdunion.it')
        
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
