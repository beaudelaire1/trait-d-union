"""Service d'envoi d'e‑mails pour les factures."""
from __future__ import annotations

from typing import Optional

from django.conf import settings
from django.core.mail import EmailMessage


class PremiumEmailService:
    """Envoi d'e‑mail avec PDF de facture en pièce jointe.

    Cette implémentation reste simple et s'appuie sur la configuration
    d'email Django (EMAIL_HOST, etc.).
    """

    def __init__(self, from_email: Optional[str] = None) -> None:
        self.from_email = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", None)

    def send_invoice_notification(self, invoice) -> bool:
        """Envoie la facture au client (et en copie à l'admin).

        - Sujet: « Facture {number} »
        - Corps: bref message avec le total TTC
        - PJ: le PDF de la facture (généré au préalable)
        """
        client_email = getattr(invoice.quote.client, "email", None)
        admin_email = getattr(settings, "ADMIN_EMAIL", None) or "contact@traitdunion.it"
        # Destinataire principal (client si disponible, sinon admin)
        recipients = [client_email] if client_email else [admin_email]

        subject = f"Facture {invoice.number} – Trait d'Union Studio"
        body = (
            f"Bonjour,\n\n"
            f"Veuillez trouver ci‑jointe votre facture {invoice.number}.\n"
            f"Montant TTC: {invoice.total_ttc} €.\n\n"
            f"Merci pour votre confiance,\n"
            f"Trait d'Union Studio"
        )

        message = EmailMessage(
            subject=subject,
            body=body,
            from_email=self.from_email,
            to=recipients,
            bcc=[admin_email] if admin_email else None,
        )

        # Joindre le PDF s'il est disponible
        if getattr(invoice, "pdf", None) and invoice.pdf:
            try:
                message.attach(invoice.pdf.name.split("/")[-1], invoice.pdf.read(), "application/pdf")
            except Exception:
                # Échec lecture du fichier: on tente de regénérer en mémoire
                pdf_bytes = invoice.generate_pdf(attach=False)
                message.attach(f"facture_{invoice.number}.pdf", pdf_bytes, "application/pdf")
        else:
            # Générer si absent
            pdf_bytes = invoice.generate_pdf(attach=False)
            message.attach(f"facture_{invoice.number}.pdf", pdf_bytes, "application/pdf")

        return bool(message.send(fail_silently=True))
