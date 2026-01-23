"""
Stripe Payment Service — Service de paiement sécurisé

Ce module gère l'intégration Stripe pour :
- Paiement d'acompte sur les devis (30% par défaut)
- Paiement du solde sur les factures
- Webhooks pour mise à jour automatique des statuts

Configuration requise (.env):
    STRIPE_SECRET_KEY=sk_live_xxx ou sk_test_xxx
    STRIPE_PUBLISHABLE_KEY=pk_live_xxx ou pk_test_xxx
    STRIPE_WEBHOOK_SECRET=whsec_xxx
"""

import os
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)

# Import conditionnel de Stripe
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    stripe = None
    STRIPE_AVAILABLE = False
    logger.warning("Stripe non installé. Les paiements en ligne sont désactivés.")


def get_stripe_keys() -> Dict[str, str]:
    """Récupère les clés Stripe depuis l'environnement."""
    return {
        'secret_key': os.environ.get('STRIPE_SECRET_KEY', ''),
        'publishable_key': os.environ.get('STRIPE_PUBLISHABLE_KEY', ''),
        'webhook_secret': os.environ.get('STRIPE_WEBHOOK_SECRET', ''),
    }


def is_stripe_configured() -> bool:
    """Vérifie si Stripe est correctement configuré."""
    if not STRIPE_AVAILABLE:
        return False
    keys = get_stripe_keys()
    return bool(keys['secret_key'] and keys['publishable_key'])


def _init_stripe():
    """Initialise le client Stripe."""
    if not STRIPE_AVAILABLE:
        raise RuntimeError("Stripe n'est pas installé.")
    keys = get_stripe_keys()
    if not keys['secret_key']:
        raise RuntimeError("STRIPE_SECRET_KEY non configurée.")
    stripe.api_key = keys['secret_key']


class StripePaymentService:
    """Service de paiement Stripe pour devis et factures."""

    # Taux d'acompte par défaut (30%)
    DEFAULT_DEPOSIT_RATE = Decimal("0.30")

    @classmethod
    def create_checkout_session_for_quote(
        cls,
        quote,
        deposit_rate: Optional[Decimal] = None,
        success_url: str = "",
        cancel_url: str = "",
    ) -> Dict[str, Any]:
        """
        Crée une session Stripe Checkout pour le paiement d'acompte d'un devis.

        Args:
            quote: Instance de Quote
            deposit_rate: Taux d'acompte (défaut 30%)
            success_url: URL de redirection après paiement réussi
            cancel_url: URL de redirection si annulation

        Returns:
            Dict contenant session_id, checkout_url, amount
        """
        _init_stripe()

        rate = deposit_rate or cls.DEFAULT_DEPOSIT_RATE
        amount_ttc = quote.total_ttc * rate
        # Stripe utilise les centimes
        amount_cents = int(amount_ttc * 100)

        # Métadonnées pour le webhook
        metadata = {
            'type': 'quote_deposit',
            'quote_id': str(quote.pk),
            'quote_number': quote.number,
            'client_email': quote.client.email,
            'deposit_rate': str(rate),
        }

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            customer_email=quote.client.email,
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': amount_cents,
                    'product_data': {
                        'name': f"Acompte Devis {quote.number}",
                        'description': f"Acompte {int(rate * 100)}% sur devis {quote.number}",
                    },
                },
                'quantity': 1,
            }],
            metadata=metadata,
            success_url=success_url or f"{settings.SITE_URL}/devis/paiement/succes/?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=cancel_url or f"{settings.SITE_URL}/devis/valider/{quote.public_token}/",
        )

        logger.info(f"Session Stripe créée pour devis {quote.number}: {session.id}")

        return {
            'session_id': session.id,
            'checkout_url': session.url,
            'amount': amount_ttc,
            'amount_cents': amount_cents,
        }

    @classmethod
    def create_checkout_session_for_invoice(
        cls,
        invoice,
        partial_amount: Optional[Decimal] = None,
        success_url: str = "",
        cancel_url: str = "",
    ) -> Dict[str, Any]:
        """
        Crée une session Stripe Checkout pour le paiement d'une facture.

        Args:
            invoice: Instance de Invoice
            partial_amount: Montant partiel (optionnel, sinon total TTC)
            success_url: URL de redirection après paiement réussi
            cancel_url: URL de redirection si annulation

        Returns:
            Dict contenant session_id, checkout_url, amount
        """
        _init_stripe()

        amount_ttc = partial_amount if partial_amount else invoice.total_ttc
        amount_cents = int(amount_ttc * 100)

        # Récupérer l'email du client via le devis lié
        client_email = ""
        if invoice.quote and invoice.quote.client:
            client_email = invoice.quote.client.email

        metadata = {
            'type': 'invoice_payment',
            'invoice_id': str(invoice.pk),
            'invoice_number': invoice.number,
            'client_email': client_email,
            'is_partial': str(partial_amount is not None).lower(),
        }

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            customer_email=client_email or None,
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': amount_cents,
                    'product_data': {
                        'name': f"Facture {invoice.number}",
                        'description': f"Paiement facture {invoice.number}",
                    },
                },
                'quantity': 1,
            }],
            metadata=metadata,
            success_url=success_url or f"{settings.SITE_URL}/factures/paiement/succes/?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=cancel_url or f"{settings.SITE_URL}/factures/paiement/annule/?token={invoice.public_token}",
        )

        logger.info(f"Session Stripe créée pour facture {invoice.number}: {session.id}")

        return {
            'session_id': session.id,
            'checkout_url': session.url,
            'amount': amount_ttc,
            'amount_cents': amount_cents,
        }

    @classmethod
    def verify_webhook_signature(cls, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """
        Vérifie la signature d'un webhook Stripe.

        Args:
            payload: Corps brut de la requête
            sig_header: Header Stripe-Signature

        Returns:
            Event Stripe décodé

        Raises:
            ValueError: Si signature invalide
        """
        _init_stripe()
        keys = get_stripe_keys()

        if not keys['webhook_secret']:
            raise ValueError("STRIPE_WEBHOOK_SECRET non configuré.")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, keys['webhook_secret']
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Signature webhook invalide: {e}")
            raise ValueError("Signature webhook invalide.")

    @classmethod
    def handle_checkout_completed(cls, session: Dict[str, Any]) -> bool:
        """
        Traite un événement checkout.session.completed.

        Met à jour le statut du devis ou de la facture selon les métadonnées.

        Returns:
            True si traitement réussi
        """
        metadata = session.get('metadata', {})
        payment_type = metadata.get('type', '')

        if payment_type == 'quote_deposit':
            return cls._handle_quote_deposit_paid(metadata, session)
        elif payment_type == 'invoice_payment':
            return cls._handle_invoice_paid(metadata, session)
        else:
            logger.warning(f"Type de paiement inconnu: {payment_type}")
            return False

    @classmethod
    def _handle_quote_deposit_paid(cls, metadata: Dict, session: Dict) -> bool:
        """Marque un devis comme accepté après paiement de l'acompte."""
        from apps.devis.models import Quote

        quote_id = metadata.get('quote_id')
        if not quote_id:
            logger.error("quote_id manquant dans les métadonnées")
            return False

        try:
            quote = Quote.objects.get(pk=int(quote_id))
            quote.status = Quote.QuoteStatus.ACCEPTED
            quote.save(update_fields=['status'])
            logger.info(f"Devis {quote.number} marqué comme ACCEPTÉ (paiement acompte)")

            # Envoyer email de confirmation au client
            from core.services.payment_email_service import send_quote_deposit_confirmation_email
            send_quote_deposit_confirmation_email(quote)

            return True
        except Quote.DoesNotExist:
            logger.error(f"Devis {quote_id} introuvable")
            return False

    @classmethod
    def _handle_invoice_paid(cls, metadata: Dict, session: Dict) -> bool:
        """Marque une facture comme payée."""
        from apps.factures.models import Invoice

        invoice_id = metadata.get('invoice_id')
        if not invoice_id:
            logger.error("invoice_id manquant dans les métadonnées")
            return False

        try:
            invoice = Invoice.objects.get(pk=int(invoice_id))
            # Vérifier si paiement partiel
            is_partial = metadata.get('is_partial', 'false') == 'true'

            if is_partial:
                invoice.status = Invoice.InvoiceStatus.PARTIAL
            else:
                invoice.status = Invoice.InvoiceStatus.PAID

            invoice.save(update_fields=['status'])
            logger.info(f"Facture {invoice.number} marquée comme {'PARTIEL' if is_partial else 'PAYÉE'}")

            # Envoyer email de confirmation
            from core.services.payment_email_service import send_invoice_payment_confirmation_email
            send_invoice_payment_confirmation_email(invoice, is_partial=is_partial)

            return True
        except Invoice.DoesNotExist:
            logger.error(f"Facture {invoice_id} introuvable")
            return False

    @classmethod
    def retrieve_session(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """Récupère les détails d'une session Checkout."""
        _init_stripe()
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Erreur récupération session {session_id}: {e}")
            return None
