from __future__ import annotations

import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

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
    try:
        res = start_quote_validation(quote, request=request)
    except QuoteNotValidatableError:
        messages.error(request, "Ce devis ne peut pas être validé dans son état actuel.")
        return redirect("devis:quote_success")
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
