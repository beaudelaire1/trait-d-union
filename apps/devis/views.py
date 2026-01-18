from __future__ import annotations

import json
import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone

from services.models import Service
from .forms import QuoteRequestForm, QuoteAdminForm
from .models import QuoteRequest, Quote, QuoteRequestPhoto, QuoteValidation
from .services import create_invoice_from_quote
from .email_service import send_quote_email
from .forms import QuoteValidationCodeForm
from apps.devis.application.quote_validation import (
    QuoteNotValidatableError,
    QuoteValidationExpiredError,
    confirm_quote_validation_code,
    start_quote_validation,
)

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def public_devis(request):
    """Formulaire public : création d'une QuoteRequest."""
    if request.method == "POST":
        form = QuoteRequestForm(request.POST, request.FILES)
        if form.is_valid():
            qr: QuoteRequest = form.save()
            files = form.cleaned_data.get("photos_list") or []
            for f in files:
                photo = QuoteRequestPhoto.objects.create(image=f)
                qr.photos.add(photo)
            messages.success(request, "Votre demande de devis a bien été envoyée.")
            return redirect("devis:quote_success")
    else:
        form = QuoteRequestForm()
    return render(request, "devis/request_quote.html", {"form": form})


def quote_success(request):
    return render(request, "devis/quote_success.html")


@staff_member_required
def download_quote_pdf(request, pk):
    """Download quote PDF - generates fresh PDF on demand.
    
    Note: On Render, filesystem is ephemeral, so we always generate fresh.
    """
    quote = get_object_or_404(Quote, pk=pk)
    
    try:
        # Always generate fresh PDF (ephemeral filesystem on Render)
        pdf_bytes = quote.generate_pdf(attach=False)
        
        # Return as response
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response['Content-Disposition'] = f'inline; filename="devis_{quote.number}.pdf"'
        return response
    except Exception as exc:
        logger.error(f"Erreur lors de la génération du PDF pour le devis {pk}: {exc}", exc_info=True)
        raise Http404("Impossible de générer le PDF du devis")


@staff_member_required
@require_http_methods(["GET", "POST"])
def admin_quote_edit(request, pk):
    """Éditeur back-office simple : métadonnées devis + actions."""
    quote = get_object_or_404(Quote, pk=pk)
    if request.method == "POST":
        form = QuoteAdminForm(request.POST, instance=quote)
        action = request.POST.get("_action")
        if form.is_valid():
            form.save()
            if action == "generate_pdf":
                quote.generate_pdf(attach=True)
                messages.success(request, "PDF généré.")
            elif action == "send_email":
                if not quote.pdf:
                    quote.generate_pdf(attach=True)
                send_quote_email(quote, request=request)
                messages.success(request, "Email envoyé.")
            elif action == "convert_invoice":
                result = create_invoice_from_quote(quote)
                invoice = result.invoice
                messages.success(request, f"Converti en facture : {invoice.number}")
                return redirect(f"/admin/factures/invoice/{invoice.pk}/change/")
            return redirect("devis:admin_quote_edit", pk=quote.pk)
    else:
        form = QuoteAdminForm(instance=quote)
    return render(request, "devis/admin_quote_edit.html", {"form": form, "quote": quote})


@staff_member_required
def service_info(request, pk):
    srv = get_object_or_404(Service, pk=pk)
    return JsonResponse({
        "id": srv.pk,
        "name": getattr(srv, "name", str(srv)),
        "description": getattr(srv, "description", ""),
        "base_price": str(getattr(srv, "base_price", "")),
        "tax_rate": str(getattr(srv, "tax_rate", "")),
    })

@staff_member_required
def admin_generate_quote_pdf(request, pk):
    quote = get_object_or_404(Quote, pk=pk)

    if hasattr(quote, "generate_pdf"):
        quote.generate_pdf(attach=True)
        messages.success(request, "Devis PDF généré avec succès.")
    else:
        messages.error(request, "La génération PDF n’est pas disponible.")

    return redirect(
        "admin:devis_quote_change",
        object_id=quote.pk,
    )


# ---------------------------------------------------------------------------
# Validation devis (double facteur)
# ---------------------------------------------------------------------------

@require_http_methods(["GET"])
def quote_validate_start(request, token: str):
    """Étape 1 : lien de validation (public) -> génération + envoi du code.

    Le paramètre ``token`` est le ``Quote.public_token`` (stable).
    """
    quote = get_object_or_404(Quote, public_token=token)
    
    # Si le devis est déjà accepté, rediriger vers la page appropriée
    if quote.status == Quote.QuoteStatus.ACCEPTED:
        messages.info(request, "Ce devis a déjà été accepté.")
        return render(request, "devis/already_signed.html", {"quote": quote})
    
    # Si le devis est facturé, afficher un message approprié
    if quote.status == Quote.QuoteStatus.INVOICED:
        messages.info(request, "Ce devis a déjà été facturé.")
        return render(request, "devis/already_signed.html", {"quote": quote})
    
    # Si le devis est rejeté, afficher un message
    if quote.status == Quote.QuoteStatus.REJECTED:
        messages.error(request, "Ce devis a été refusé et ne peut plus être validé.")
        return render(request, "devis/quote_unavailable.html", {"quote": quote})
    
    # Si le devis est en brouillon (pas encore envoyé)
    if quote.status == Quote.QuoteStatus.DRAFT:
        messages.error(request, "Ce devis n'a pas encore été finalisé. Veuillez nous contacter.")
        return render(request, "devis/quote_unavailable.html", {"quote": quote})
    
    try:
        res = start_quote_validation(quote, request=request)
    except QuoteNotValidatableError:
        messages.error(request, "Ce devis ne peut pas être validé dans son état actuel.")
        return render(request, "devis/quote_unavailable.html", {"quote": quote})
    return redirect("devis:quote_validate_code", token=res.validation.token)


@require_http_methods(["GET", "POST"])
def quote_validate_code(request, token: str):
    """Étape 2 : saisie du code -> validation finale."""
    validation = get_object_or_404(QuoteValidation, token=token)
    quote = validation.quote

    if validation.is_expired:
        messages.error(request, "Ce code a expiré. Merci de relancer une validation.")
        return render(request, "devis/validate_expired.html", {"quote": quote})

    if request.method == "POST":
        form = QuoteValidationCodeForm(request.POST)
        if form.is_valid():
            try:
                ok = confirm_quote_validation_code(validation=validation, submitted_code=form.cleaned_data["code"])
            except QuoteValidationExpiredError:
                ok = False
                messages.error(request, "Ce code a expiré. Merci de relancer une validation.")
                return render(request, "devis/validate_expired.html", {"quote": quote})

            if ok:
                messages.success(request, "Merci ! Votre devis est validé.")
                return render(request, "devis/validate_success.html", {"quote": quote})

            messages.error(request, "Code incorrect. Veuillez réessayer.")
    else:
        form = QuoteValidationCodeForm()

    return render(
        request,
        "devis/validate_code.html",
        {"quote": quote, "form": form, "validation": validation},
    )


@require_http_methods(["GET"])
def quote_public_pdf(request, token: str):
    """Téléchargement public du PDF via un jeton *stable*.

    Historique:
    - v1: le lien pointait vers QuoteValidation.token (peut expirer / être régénéré)
    - v2+: le lien public pointe vers Quote.public_token (stable)
    Pour compatibilité, on accepte encore un token de QuoteValidation si nécessaire.
    """
    quote = None
    # 1) Token public stable du devis
    try:
        quote = Quote.objects.get(public_token=token)
    except Exception:
        quote = None

    # 2) Compatibilité: ancien token de validation 2FA
    if quote is None:
        validation = get_object_or_404(QuoteValidation, token=token)
        if validation.is_expired:
            raise Http404()
        quote = validation.quote

    try:
        # Always generate fresh PDF (ephemeral filesystem on Render)
        pdf_bytes = quote.generate_pdf(attach=False)
        
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
        response['Content-Disposition'] = f'inline; filename="devis_{quote.number}.pdf"'
        return response
    except Exception as exc:
        logger.error(f"Erreur lors de la génération du PDF public pour le token {token}: {exc}", exc_info=True)
        raise Http404("Impossible de générer le PDF du devis")


# ---------------------------------------------------------------------------
# PHASE 3 : Paiement Stripe & Signature électronique
# ---------------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
def quote_sign_and_pay(request, token: str):
    """
    Page de signature et paiement d'acompte pour un devis.
    
    Flux:
    1. Le client voit le récapitulatif du devis
    2. Il signe électroniquement (signature_pad.js)
    3. Il paie l'acompte via Stripe Checkout
    """
    quote = get_object_or_404(Quote, public_token=token)
    
    # Vérifier que le devis peut être signé (statut SENT)
    if quote.status not in [Quote.QuoteStatus.SENT, Quote.QuoteStatus.DRAFT]:
        if quote.status == Quote.QuoteStatus.ACCEPTED:
            messages.info(request, "Ce devis a déjà été accepté.")
            return render(request, "devis/already_signed.html", {"quote": quote})
        messages.error(request, "Ce devis ne peut pas être signé dans son état actuel.")
        return redirect("pages:home")
    
    # Vérifier la validité
    if quote.valid_until and quote.valid_until < timezone.now().date():
        messages.error(request, "Ce devis a expiré.")
        return render(request, "devis/quote_expired.html", {"quote": quote})
    
    # Import des services
    from core.services.stripe_service import is_stripe_configured, get_stripe_keys
    
    context = {
        "quote": quote,
        "stripe_configured": is_stripe_configured(),
        "stripe_publishable_key": get_stripe_keys().get('publishable_key', ''),
        "deposit_rate": 30,  # 30% d'acompte
        "deposit_amount": quote.total_ttc * 30 / 100,
    }
    
    return render(request, "devis/sign_and_pay.html", context)


@require_POST
def quote_submit_signature(request, token: str):
    """
    Endpoint AJAX pour soumettre la signature électronique.
    
    Reçoit: signature_data (base64 PNG)
    Retourne: JSON avec success et éventuellement checkout_url
    """
    quote = get_object_or_404(Quote, public_token=token)
    
    # Vérifier le statut
    if quote.status not in [Quote.QuoteStatus.SENT, Quote.QuoteStatus.DRAFT]:
        return JsonResponse({
            "success": False,
            "error": "Ce devis ne peut pas être signé."
        }, status=400)
    
    # Récupérer les données
    try:
        data = json.loads(request.body)
        signature_data = data.get("signature_data", "")
    except json.JSONDecodeError:
        signature_data = request.POST.get("signature_data", "")
    
    if not signature_data:
        return JsonResponse({
            "success": False,
            "error": "Aucune signature fournie."
        }, status=400)
    
    # Valider la signature
    from core.services.signature_service import SignatureService
    
    is_valid, message = SignatureService.validate_signature_data(signature_data)
    if not is_valid:
        return JsonResponse({
            "success": False,
            "error": message
        }, status=400)
    
    # Sauvegarder la signature
    signature_hash = SignatureService.compute_signature_hash(signature_data)
    signature_path = SignatureService.save_signature_image(
        signature_data,
        filename=f"signature_{quote.number}_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
        subdir="devis/signatures"
    )
    
    # Générer l'audit trail
    audit_trail = SignatureService.generate_audit_trail(
        client_ip=SignatureService.get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown'),
        document_type='quote',
        document_id=str(quote.pk),
        document_number=quote.number,
        signer_name=quote.client.full_name if quote.client else 'Client',
        signer_email=quote.client.email if quote.client else '',
        signature_hash=signature_hash,
    )
    
    # Mettre à jour le devis
    if signature_path:
        quote.signature_image = signature_path
    quote.signed_at = timezone.now()
    quote.signature_audit_trail = audit_trail
    quote.save(update_fields=['signature_image', 'signed_at', 'signature_audit_trail'])
    
    # Créer la session Stripe si configuré
    from core.services.stripe_service import is_stripe_configured, StripePaymentService
    
    response_data = {
        "success": True,
        "message": "Signature enregistrée avec succès.",
    }
    
    if is_stripe_configured():
        try:
            from django.conf import settings
            session_data = StripePaymentService.create_checkout_session_for_quote(
                quote,
                success_url=f"{settings.SITE_URL}/devis/paiement/succes/?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.SITE_URL}/devis/valider/{quote.public_token}/signer/",
            )
            quote.stripe_checkout_session_id = session_data['session_id']
            quote.save(update_fields=['stripe_checkout_session_id'])
            
            response_data["checkout_url"] = session_data['checkout_url']
            response_data["requires_payment"] = True
        except Exception as e:
            logger.error(f"Erreur création session Stripe: {e}")
            # La signature est quand même valide
            response_data["requires_payment"] = False
            response_data["message"] = "Signature enregistrée. Paiement non disponible pour le moment."
    else:
        response_data["requires_payment"] = False
        # Marquer comme accepté directement si pas de paiement
        quote.status = Quote.QuoteStatus.ACCEPTED
        quote.save(update_fields=['status'])
    
    return JsonResponse(response_data)


@require_http_methods(["GET"])
def quote_payment_success(request):
    """
    Page de confirmation après paiement réussi.
    """
    session_id = request.GET.get('session_id', '')
    
    if not session_id:
        return redirect("pages:home")
    
    # Récupérer la session Stripe
    from core.services.stripe_service import StripePaymentService, is_stripe_configured
    
    quote = None
    if is_stripe_configured():
        try:
            session = StripePaymentService.retrieve_session(session_id)
            if session:
                quote_id = session.get('metadata', {}).get('quote_id')
                if quote_id:
                    quote = Quote.objects.filter(pk=int(quote_id)).first()
        except Exception as e:
            logger.error(f"Erreur récupération session: {e}")
    
    if not quote:
        # Essayer de trouver par session_id
        quote = Quote.objects.filter(stripe_checkout_session_id=session_id).first()
    
    return render(request, "devis/payment_success.html", {
        "quote": quote,
        "session_id": session_id,
    })


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Webhook Stripe pour gérer les événements de paiement.
    """
    from core.services.stripe_service import StripePaymentService, is_stripe_configured
    
    if not is_stripe_configured():
        return HttpResponse(status=400)
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    
    try:
        event = StripePaymentService.verify_webhook_signature(payload, sig_header)
    except ValueError as e:
        logger.error(f"Webhook signature invalide: {e}")
        return HttpResponse(status=400)
    
    # Traiter les événements
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        StripePaymentService.handle_checkout_completed(session)
    
    return HttpResponse(status=200)
