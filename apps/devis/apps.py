"""
Configuration de l’application ``devis`` (app modernisée).

Cette app remplace l’ancienne app ``quotes`` et gère les demandes de devis
pour les services NetExpress.  La configuration fournit un
``verbose_name`` afin d’afficher un libellé plus lisible dans
l’administration.  Depuis 2025, cette app est la référence pour créer
et suivre des devis.
"""

from django.apps import AppConfig


class DevisConfig(AppConfig):
    """AppConfig pour la gestion des devis modernisés."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "devis"
    verbose_name = "Devis"

    def ready(self) -> None:
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
