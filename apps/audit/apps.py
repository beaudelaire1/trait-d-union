"""Configuration de l'app audit."""
from django.apps import AppConfig


class AuditConfig(AppConfig):
    """Configuration pour l'app audit."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audit'
    verbose_name = 'Audit & traçabilité'
