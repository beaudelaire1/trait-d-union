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
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
