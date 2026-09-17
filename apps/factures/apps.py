"""
Configuration de l’app ``factures``.

Cette application contient l’implémentation moderne de la gestion des
factures (factures multi‑lignes, statuts, génération de PDF).  Elle
remplace l’ancienne app ``invoices`` et adopte la charte graphique et
les conventions de 2025.  Le ``verbose_name`` est défini pour une
apparition lisible dans l’interface d’administration.
"""

from django.apps import AppConfig


class FacturesConfig(AppConfig):
    """AppConfig pour l’app moderne de facturation."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.factures"
    verbose_name = "Factures"

    def ready(self) -> None:
        # Signaux de notification gérés dans apps/clients/signals.py
        #
        # Les anciens modèles ajoutent littéralement « euros » après une
        # conversion générique du nombre. Pour les documents financiers,
        # on remplace cette représentation par une vraie écriture monétaire
        # (« 24,48 € » -> « vingt-quatre euros et quarante-huit centimes »).
        from core.utils import amount_to_words_fr
        from .models import Invoice

        def amount_letter(invoice):
            return amount_to_words_fr(invoice.total_ttc).title()

        Invoice.amount_letter = amount_letter
