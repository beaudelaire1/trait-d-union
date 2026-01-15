"""
Routes URL pour l'application ``factures``.

Deux routes sont exposées aux membres du staff :

* ``create/<int:quote_id>/`` pour créer une facture à partir d'un devis.
* ``download/<int:pk>/`` pour télécharger le PDF d'une facture existante.
"""

from django.urls import path
from . import views


app_name = "factures"

urlpatterns = [
    path("create/<int:quote_id>/", views.create_invoice, name="create"),
    path("download/<int:pk>/", views.download_invoice, name="download"),
    # Liste des factures avec leurs fichiers PDF (archive)
    path("archive/", views.archive, name="archive"),
]