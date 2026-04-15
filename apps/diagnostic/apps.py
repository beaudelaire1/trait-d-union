"""App configuration for the diagnostic tool."""
from django.apps import AppConfig


class DiagnosticConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.diagnostic"
    verbose_name = "Diagnostic de site"
