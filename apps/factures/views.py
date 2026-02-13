"""
Vues pour la gestion des factures.
Rationalisation : retrait de la couche expérimentale hexcore pour revenir à une approche Django pure.
"""

import json
import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone

from apps.devis.models import Quote
from .models import Invoice

logger = logging.getLogger(__name__)


@staff_member_required
def create_invoice(request, quote_id: int):
    """
    Crée une facture à partir d'un devis existant.
    Utilise le service de conversion Quote → Invoice.
    """
    quote = get_object_or_404(Quote, pk=quote_id)
    
    try:
        # Création de la facture via le service dédi é
        from apps.devis.services import create_invoice_from_quote
        result = create_invoice_from_quote(quote)
        invoice = result.invoice
        
        # Génération du PDF
        invoice.generate_pdf(attach=True)
        
        messages.success(request, f"La facture {invoice.number} a été créée avec succès.")
        
        # Alerte si la facture est vide
        if not invoice.invoice_items.exists():
            messages.warning(request, "Attention : la facture créée ne contient aucune ligne.")
            
    except Exception as e:
        logger.error(f"Erreur lors de la création de facture depuis devis {quote_id}: {e}", exc_info=True)
        messages.error(request, f"Erreur lors de la création de la facture : {str(e)}")
        
    return redirect(reverse("factures:archive"))


@staff_member_required
def download_invoice(request, pk: int):
    """
    Téléchargement du PDF de la facture.
    
    Note: On Render, filesystem is ephemeral, so we always generate fresh.
    """
    invoice = get_object_or_404(Invoice, pk=pk)
    
    try:
        # Always generate fresh PDF (ephemeral filesystem on Render)
        pdf_bytes = invoice.generate_pdf(attach=False)
        
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response['Content-Disposition'] = f'inline; filename="facture_{invoice.number}.pdf"'
        return response
    except Exception as exc:
        logger.error(f"Erreur lors de la génération du PDF pour la facture {pk}: {exc}", exc_info=True)
        raise Http404("Impossible de générer le PDF de la facture")


@staff_member_required
def archive(request):
    """
    Archive des factures.
    """
    invoices = Invoice.objects.all().order_by("-issue_date", "-number")
    return render(request, "factures/archive.html", {"invoices": invoices})


# ===========================================
# PHASE 3 : Paiement en ligne des factures
# ===========================================

@require_http_methods(["GET"])
def invoice_pay(request, token: str):
    """
    Page de paiement d'une facture via lien public.
    """
    invoice = get_object_or_404(Invoice, public_token=token)
    
    # Vérifier que la facture peut être payée
    if invoice.status == Invoice.InvoiceStatus.PAID:
        return render(request, "factures/already_paid.html", {"invoice": invoice})
    
    if invoice.status not in [Invoice.InvoiceStatus.SENT, Invoice.InvoiceStatus.PARTIAL, Invoice.InvoiceStatus.OVERDUE]:
        messages.error(request, "Cette facture ne peut pas être payée en ligne.")
        return redirect("pages:home")
    
    # Calculer le reste à payer
    remaining = invoice.total_ttc - (invoice.amount_paid or 0)
    
    # Import des services Stripe
    from core.services.stripe_service import is_stripe_configured, get_stripe_keys
    
    context = {
        "invoice": invoice,
        "remaining": remaining,
        "stripe_configured": is_stripe_configured(),
        "stripe_publishable_key": get_stripe_keys().get('publishable_key', ''),
    }
    
    return render(request, "factures/pay.html", context)


@require_POST
def invoice_create_checkout(request, token: str):
    """
    Crée une session Stripe Checkout pour le paiement d'une facture.
    """
    invoice = get_object_or_404(Invoice, public_token=token)
    
    # Vérifier le statut
    if invoice.status == Invoice.InvoiceStatus.PAID:
        return JsonResponse({
            "success": False,
            "error": "Cette facture est déjà payée."
        }, status=400)
    
    from core.services.stripe_service import is_stripe_configured, StripePaymentService
    
    if not is_stripe_configured():
        return JsonResponse({
            "success": False,
            "error": "Le paiement en ligne n'est pas disponible."
        }, status=400)
    
    # Calculer le montant à payer
    remaining = invoice.total_ttc - (invoice.amount_paid or 0)
    
    try:
        from django.conf import settings
        session_data = StripePaymentService.create_checkout_session_for_invoice(
            invoice,
            partial_amount=remaining if invoice.amount_paid > 0 else None,
            success_url=f"{settings.SITE_URL}/factures/paiement/succes/?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.SITE_URL}/factures/payer/{invoice.public_token}/",
        )
        
        invoice.stripe_checkout_session_id = session_data['session_id']
        invoice.save(update_fields=['stripe_checkout_session_id'])
        
        return JsonResponse({
            "success": True,
            "checkout_url": session_data['checkout_url'],
        })
        
    except Exception as e:
        logger.error(f"Erreur création session Stripe facture: {e}")
        return JsonResponse({
            "success": False,
            "error": "Une erreur est survenue. Veuillez réessayer."
        }, status=500)


@require_http_methods(["GET"])
def invoice_payment_success(request):
    """
    Page de confirmation après paiement d'une facture.
    """
    session_id = request.GET.get('session_id', '')
    
    if not session_id:
        return redirect("pages:home")
    
    # Récupérer la facture
    from core.services.stripe_service import StripePaymentService, is_stripe_configured
    
    invoice = None
    if is_stripe_configured():
        try:
            session = StripePaymentService.retrieve_session(session_id)
            if session:
                invoice_id = session.get('metadata', {}).get('invoice_id')
                if invoice_id:
                    invoice = Invoice.objects.filter(pk=int(invoice_id)).first()
        except Exception as e:
            logger.error(f"Erreur récupération session facture: {e}")
    
    if not invoice:
        invoice = Invoice.objects.filter(stripe_checkout_session_id=session_id).first()
    
    return render(request, "factures/payment_success.html", {
        "invoice": invoice,
        "session_id": session_id,
    })


@require_http_methods(["GET"])
def invoice_payment_cancel(request):
    """
    Page affichée quand le client annule le paiement sur Stripe.
    """
    token = request.GET.get('token', '')
    invoice = None
    
    if token:
        invoice = Invoice.objects.filter(public_token=token).first()
    
    return render(request, "factures/payment_cancel.html", {
        "invoice": invoice,
    })


@require_http_methods(["GET"])
def invoice_payment_error(request):
    """
    Page affichée en cas d'erreur de paiement.
    """
    token = request.GET.get('token', '')
    error_message = request.GET.get('error', '')
    invoice = None
    
    if token:
        invoice = Invoice.objects.filter(public_token=token).first()
    
    return render(request, "factures/payment_error.html", {
        "invoice": invoice,
        "error_message": error_message,
    })


@require_http_methods(["GET"])
def invoice_public_pdf(request, token: str):
    """
    Téléchargement public du PDF de facture via jeton.
    """
    invoice = get_object_or_404(Invoice, public_token=token)
    
    try:
        pdf_bytes = invoice.generate_pdf(attach=False)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response['Content-Disposition'] = f'inline; filename="facture_{invoice.number}.pdf"'
        return response
    except Exception as exc:
        logger.error(f"Erreur génération PDF facture publique: {exc}", exc_info=True)
        raise Http404("Impossible de générer le PDF de la facture")


@csrf_exempt
@require_POST
def stripe_invoice_webhook(request):
    """
    Webhook Stripe pour les paiements de factures.
    """
    from core.services.stripe_service import StripePaymentService, is_stripe_configured
    
    if not is_stripe_configured():
        return HttpResponse(status=400)
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    
    try:
        event = StripePaymentService.verify_webhook_signature(payload, sig_header)
    except ValueError as e:
        logger.error(f"Webhook facture signature invalide: {e}")
        return HttpResponse(status=400)
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        StripePaymentService.handle_checkout_completed(session)
    
    return HttpResponse(status=200)
