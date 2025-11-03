from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.account"
    
    def ready(self):
        import apps.account.signals  # noqa
