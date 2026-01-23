from django.apps import AppConfig


class ClientsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.clients'
    verbose_name = 'Espace Client'
    
    def ready(self):
        """Import signals when app is ready."""
        import apps.clients.signals  # noqa
