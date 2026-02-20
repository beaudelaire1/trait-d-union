"""Email service for payment confirmations."""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_quote_deposit_confirmation_email(quote):
    """Send confirmation email after quote deposit payment."""
    try:
        context = {
            'quote': quote,
            'client_name': quote.client.full_name,
            'quote_number': quote.number,
            'site_url': settings.SITE_URL,
        }
        
        html_content = render_to_string('emails/quote_deposit_confirmation.html', context)
        text_content = f"""
Bonjour {quote.client.full_name},

Nous avons bien reçu votre paiement d'acompte pour le devis {quote.number}.

Votre projet démarre ! Nous vous tiendrons informé de l'avancement.

Cordialement,
L'équipe Trait d'Union Studio
        """
        
        email = EmailMultiAlternatives(
            subject=f'Paiement reçu - Devis {quote.number}',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[quote.client.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur envoi email confirmation devis: {e}")
        return False


def send_invoice_payment_confirmation_email(invoice, is_partial=False):
    """Send confirmation email after invoice payment."""
    try:
        remaining_balance = invoice.total_ttc - (invoice.amount_paid or 0)
        context = {
            'invoice': invoice,
            'is_partial': is_partial,
            'client_name': invoice.quote.client.full_name if invoice.quote else 'Client',
            'invoice_number': invoice.number,
            'amount': invoice.amount_paid,
            'remaining_balance': remaining_balance,
            'site_url': settings.SITE_URL,
        }
        
        html_content = render_to_string('emails/invoice_payment_confirmation.html', context)
        
        if is_partial:
            subject = f'Paiement partiel reçu - Facture {invoice.number}'
            text_content = f"""
Bonjour,

Nous avons bien reçu votre paiement partiel de {invoice.amount_paid}€ pour la facture {invoice.number}.

Solde restant : {invoice.total_ttc - invoice.amount_paid}€

Cordialement,
L'équipe Trait d'Union Studio
            """
        else:
            subject = f'Paiement reçu - Facture {invoice.number}'
            text_content = f"""
Bonjour,

Nous avons bien reçu votre paiement de {invoice.amount_paid}€ pour la facture {invoice.number}.

Votre facture est soldée. Merci pour votre confiance !

Cordialement,
L'équipe Trait d'Union Studio
            """
        
        email_to = invoice.quote.client.email if invoice.quote else settings.ADMIN_EMAIL
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email_to],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur envoi email confirmation facture: {e}")
        return False
