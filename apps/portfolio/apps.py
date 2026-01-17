"""Portfolio app configuration."""
from django.apps import AppConfig


class PortfolioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.portfolio'
    verbose_name = 'Portfolio'

    def ready(self):
        """Import signals pour la conversion WebP automatique."""
        from . import signals  # noqa: F401
