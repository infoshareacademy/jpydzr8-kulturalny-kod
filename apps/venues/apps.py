from django.apps import AppConfig


class VenuesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.venues"
    label = "venues"
    verbose_name = "Venues"
