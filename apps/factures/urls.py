"""
Routes URL pour l'application ``factures``.

Deux routes sont exposées aux membres du staff :

* ``create/<int:quote_id>/`` pour créer une facture à partir d'un devis.
* ``download/<int:pk>/`` pour télécharger le PDF d'une facture existante.

Routes publiques (Phase 3 - Paiement en ligne):
* ``payer/<token>/`` pour accéder à la page de paiement d'une facture.
"""

from django.urls import path
from . import views


app_name = "factures"

urlpatterns = [
    path("create/<int:quote_id>/", views.create_invoice, name="create"),
    path("download/<int:pk>/", views.download_invoice, name="download"),
    # Liste des factures avec leurs fichiers PDF (archive)
    path("archive/", views.archive, name="archive"),
    
    # ===========================================
    # PHASE 3 : Paiement en ligne
    # ===========================================
    path("payer/<str:token>/", views.invoice_pay, name="pay"),
    path("payer/<str:token>/checkout/", views.invoice_create_checkout, name="create_checkout"),
    path("paiement/succes/", views.invoice_payment_success, name="payment_success"),
    path("paiement/annule/", views.invoice_payment_cancel, name="payment_cancel"),
    path("paiement/erreur/", views.invoice_payment_error, name="payment_error"),
    path("pdf/<str:token>/", views.invoice_public_pdf, name="public_pdf"),
    path("webhook/stripe/", views.stripe_invoice_webhook, name="stripe_webhook"),
]