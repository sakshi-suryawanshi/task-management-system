from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    App configuration for core app.
    
    This configuration ensures that signals are loaded when the app is ready.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'

    def ready(self):
        """Import signals when the app is ready."""
        import core.signals  # noqa
