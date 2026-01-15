"""
Vues pour la gestion des factures.
Rationalisation : retrait de la couche expérimentale hexcore pour revenir à une approche Django pure.
"""

import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from apps.devis.models import Quote
from .models import Invoice

logger = logging.getLogger(__name__)


@staff_member_required
def create_invoice(request, quote_id: int):
    """
    Crée une facture à partir d'un devis existant.
    Approche directe via le modèle Invoice.
    """
    quote = get_object_or_404(Quote, pk=quote_id)
    
    try:
        # Création de la facture via la méthode de classe du modèle
        invoice = Invoice.create_from_quote(quote)
        
        # Génération du PDF
        invoice.generate_pdf(attach=True)
        
        messages.success(request, f"La facture {invoice.number} a été créée avec succès.")
        
        # Alerte si la facture est vide
        if not invoice.invoice_items.exists():
            messages.warning(request, "Attention : la facture créée ne contient aucune ligne.")
            
    except Exception as e:
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
