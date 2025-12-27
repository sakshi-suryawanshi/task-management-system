from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Configuration for the users app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Users'
    
    def ready(self):
        """Import signals when app is ready."""
        import users.signals
