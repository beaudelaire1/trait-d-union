"""Service d'envoi d'emails pour les factures."""
from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class PremiumEmailService:
    """Envoi d'email avec PDF de facture en pièce jointe.

    Cette implémentation utilise Brevo si configuré, sinon fallback Django.
    """

    def __init__(self, from_email: Optional[str] = None) -> None:
        self.from_email = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", None)
        self.from_name = getattr(settings, "DEFAULT_FROM_NAME", "Trait d'Union Studio")

    def send_invoice_notification(self, invoice) -> bool:
        """Envoie la facture au client (et en copie à l'admin).

        - Sujet: « Facture {number} »
        - Corps: bref message avec le total TTC
        - PJ: le PDF de la facture (généré au préalable)
        """
        client_email = getattr(invoice.quote.client, "email", None)
        admin_email = getattr(settings, "ADMIN_EMAIL", None) or "contact@traitdunion.it"
        
        # Destinataire principal (client si disponible, sinon admin)
        recipient = client_email if client_email else admin_email
        
        subject = f"Facture {invoice.number} – Trait d'Union Studio"
        
        # Corps HTML pour Brevo
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">Votre facture {invoice.number}</h2>
            <p>Bonjour,</p>
            <p>Veuillez trouver ci-jointe votre facture <strong>{invoice.number}</strong>.</p>
            <p style="font-size: 18px; background: #f5f5f5; padding: 15px; border-radius: 5px;">
                Montant TTC: <strong>{invoice.total_ttc} €</strong>
            </p>
            <p>Merci pour votre confiance.</p>
            <p style="color: #666; margin-top: 30px;">
                Trait d'Union Studio<br>
                <a href="https://traitdunion.it">traitdunion.it</a>
            </p>
        </div>
        """
        
        text_body = (
            f"Bonjour,\n\n"
            f"Veuillez trouver ci-jointe votre facture {invoice.number}.\n"
            f"Montant TTC: {invoice.total_ttc} €.\n\n"
            f"Merci pour votre confiance,\n"
            f"Trait d'Union Studio"
        )

        # Générer le PDF
        pdf_bytes = None
        pdf_filename = f"facture_{invoice.number}.pdf"
        
        if getattr(invoice, "pdf", None) and invoice.pdf:
            try:
                pdf_bytes = invoice.pdf.read()
                pdf_filename = invoice.pdf.name.split("/")[-1]
            except Exception:
                pass
        
        if not pdf_bytes:
            try:
                pdf_bytes = invoice.generate_pdf(attach=False)
            except Exception as e:
                logger.error(f"Erreur génération PDF facture {invoice.number}: {e}")

        # Préparer les pièces jointes
        attachments = []
        if pdf_bytes:
            attachments.append({
                'name': pdf_filename,
                'content': pdf_bytes,
                'mime_type': 'application/pdf'
            })

        # Envoyer via Brevo ou fallback Django
        try:
            from core.services.email_backends import send_simple_email, brevo_service
            
            if brevo_service.is_configured():
                # Utiliser l'API Brevo avec HTML
                from core.services.email_backends import send_transactional_email
                
                result = send_transactional_email(
                    to_email=recipient,
                    subject=subject,
                    html_content=html_body,
                    from_email=self.from_email,
                    from_name=self.from_name,
                    attachments=attachments if attachments else None,
                    tags=['facture', 'invoice', f'invoice-{invoice.number}']
                )
                
                # Envoyer copie à l'admin si client est le destinataire principal
                if client_email and admin_email and client_email != admin_email:
                    send_transactional_email(
                        to_email=admin_email,
                        subject=f"[Copie] {subject}",
                        html_content=html_body,
                        from_email=self.from_email,
                        from_name=self.from_name,
                        attachments=attachments if attachments else None,
                        tags=['facture', 'invoice', 'admin-copy']
                    )
                
                success = result.get('success', False)
                if success:
                    logger.info(f"Facture {invoice.number} envoyée via Brevo à {recipient}")
                return success
            else:
                # Fallback Django
                return send_simple_email(
                    to_email=recipient,
                    subject=subject,
                    text_body=text_body,
                    html_body=html_body,
                    from_email=self.from_email,
                    attachments=attachments if attachments else None,
                    bcc=[admin_email] if client_email and admin_email else None
                )
                
        except ImportError:
            # Ultime fallback avec Django EmailMessage
            from django.core.mail import EmailMessage
            
            message = EmailMessage(
                subject=subject,
                body=text_body,
                from_email=self.from_email,
                to=[recipient],
                bcc=[admin_email] if admin_email and recipient != admin_email else None,
            )
            
            if attachments:
                for att in attachments:
                    message.attach(att['name'], att['content'], att.get('mime_type', 'application/pdf'))
            
            return bool(message.send(fail_silently=True))
