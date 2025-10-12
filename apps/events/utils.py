import os
import json
from datetime import datetime
from .models import Event

def load_events_from_json(filepath):
    if not os.path.exists(filepath):
        print(f"Plik {filepath} nie istnieje.")
        return

    if Event.objects.exists():
        print("Wydarzenia już istnieją w bazie. Pomijam import.")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Błąd przy wczytywaniu JSON: {e}")
            return

    for item in data:
        try:
            Event.objects.create(
                name=item["name"],
                date=datetime.strptime(item["date"], "%Y-%m-%d"),
                city=item["city"],
                venue=item["venue"],
                total_seats=item["total_seats"],
                available_seats=item["available_seats"],
                price=item["price"],
                description=item["description"],
                highlights=item["highlights"],
            )
        except Exception as e:
            print(f"Błąd przy zapisie eventu: {e}")