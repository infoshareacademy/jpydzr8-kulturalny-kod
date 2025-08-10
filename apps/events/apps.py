from django.apps import AppConfig
import os
import sys

class EventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.events'

    def ready(self):
        if 'runserver' in sys.argv:
            from .utils import load_events_from_json
            from django.conf import settings
            path = os.path.join(settings.BASE_DIR, 'apps/events/static/json_files/events.json')
            load_events_from_json(path)