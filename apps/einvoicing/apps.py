"""AppConfig for the e-invoicing compliance app."""

from django.apps import AppConfig


class EInvoicingConfig(AppConfig):
    default = True  # Force Django à charger ce config (sinon ready() pas appelé)
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.einvoicing"
    label = "einvoicing"
    verbose_name = "Facturation électronique (FR)"

    def ready(self) -> None:  # pragma: no cover - signal wiring
        # Import signal handlers to register them.
        from . import signals  # noqa: F401
