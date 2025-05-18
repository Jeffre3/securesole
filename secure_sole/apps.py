from django.apps import AppConfig

class SecureSoleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'secure_sole'

    def ready(self):
        import store.signals
