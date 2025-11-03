import json
import os
from datetime import datetime, time
from django.utils import timezone

from .models import Event
from apps.venues.models import Venue, VenueArea, SeatingPlan


def load_events_from_json(filepath):
    if not os.path.exists(filepath):
        print(f"Plik {filepath} nie istnieje.")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Błąd przy wczytywaniu JSON: {e}")
            return

    tz = timezone.get_current_timezone()
    created_events = 0

    for item in data:
        venue_name = item["venue"].strip()
        city = item["city"].strip()

        venue, _ = Venue.objects.get_or_create(name=venue_name, defaults={"city": city})

        area, _ = VenueArea.objects.get_or_create(venue=venue, name="Główna")

        plan, _ = SeatingPlan.objects.get_or_create(area=area, title="Domyślny")

        dt = timezone.make_aware(datetime.strptime(item["date"], "%Y-%m-%d"), tz)

        _, created = Event.objects.update_or_create(
            name=item["name"],
            date=dt,
            defaults={
                "city": city,
                "venue_area": area,
                "seating_plan": plan,
                "price": item["price"],
                "total_seats": item["total_seats"],
                "available_seats": item["available_seats"],
                "description": item["description"],
                "highlights": item["highlights"],
            },
        )
        created_events += int(created)

    print(f"Zaimportowano nowych wydarzeń: {created_events}")
