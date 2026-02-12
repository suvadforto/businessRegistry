from django.apps import AppConfig

class RegistryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'registry'
    verbose_name = "Registar obrta"

    def ready(self):
        import registry.signals
        