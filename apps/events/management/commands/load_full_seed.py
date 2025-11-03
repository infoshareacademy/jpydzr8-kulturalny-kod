import json
import os
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.events.models import Event, EventSeat
from apps.venues.models import (
    Venue, VenueArea, SeatingPlan, Section, Seat, SectionType
)

SECTION_SPECS = [
    ("Płyta",   SectionType.STANDING, 0,   0,  0,  2000),
    ("Trybuna", SectionType.SEATED,   100, 10, 20, 0),
    ("Balkon",  SectionType.SEATED,   150, 5,  15, 0),
    ("VIP",     SectionType.SEATED,   300, 3,  10, 0),
]

DEFAULT_TIME = dt_time(20, 0)


class Command(BaseCommand):
    help = "Load events JSON and auto-create Venue/Area/Plan/Sections/Seats, then backfill EventSeat."

    def add_arguments(self, parser):
        parser.add_argument(
            "file",
            type=str,
            help="Ścieżka do pliku JSON z eventami (lista obiektów).",
        )

    def handle(self, *args, **opts):
        file_path = Path(opts["file"])
        if not file_path.exists():
            raise CommandError(f"Plik nie istnieje: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                events_data = json.load(f)
            except Exception as e:
                raise CommandError(f"Nie można wczytać JSON: {e}")

        created_events = 0
        updated_events = 0
        created_seats_total = 0
        created_event_seats_total = 0

        for i, item in enumerate(events_data, start=1):
            with transaction.atomic():
                event, was_created, seat_count, evseat_count = self._upsert_event_with_layout(item)
                created_seats_total += seat_count
                created_event_seats_total += evseat_count
                if was_created:
                    created_events += 1
                else:
                    updated_events += 1

        self.stdout.write(self.style.SUCCESS(
            f"Zakończono. Events: created={created_events}, updated={updated_events}, "
            f"Seats created={created_seats_total}, EventSeats created={created_event_seats_total}"
        ))

    def _parse_datetime(self, date_str: str, time_str: Optional[str]) -> datetime:
        """Zwraca datetime; jeśli brak time -> 20:00."""
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            d = datetime.fromisoformat(date_str).date()
        if time_str:
            try:
                hh, mm = [int(x) for x in time_str.split(":")[:2]]
                t = dt_time(hh, mm)
            except Exception:
                t = DEFAULT_TIME
        else:
            t = DEFAULT_TIME
        return datetime.combine(d, t)

    def _get_or_create_layout(self, venue_name: str, city: str) -> Tuple[Venue, VenueArea, SeatingPlan, int]:
        """Tworzy Venue, Area, SeatingPlan i standardowe Sections + Seats (wg SECTION_SPECS).
           Zwraca (venue, area, plan, liczba-nowo-utworzonych-Seat)."""
        venue, _ = Venue.objects.get_or_create(
            name=venue_name.strip(),
            city=city.strip(),
            defaults={"address": "", "pets_friendly": False, "description": ""},
        )
        area, _ = VenueArea.objects.get_or_create(venue=venue, name="Sala Główna")
        plan, _ = SeatingPlan.objects.get_or_create(area=area, title="Domyślny")

        created_seats = 0
        for name, sec_type, price_mod, rows, per_row, standing_capacity in SECTION_SPECS:
            section, _ = Section.objects.get_or_create(
                plan=plan,
                name=name,
                defaults={
                    "type": sec_type,
                    "capacity": (standing_capacity if sec_type == SectionType.STANDING else 0),
                    "price_modifier": price_mod,
                },
            )
            update_fields = []
            if section.type != sec_type:
                section.type = sec_type
                update_fields.append("type")
            if section.price_modifier != price_mod:
                section.price_modifier = price_mod
                update_fields.append("price_modifier")
            if sec_type == SectionType.STANDING and section.capacity != standing_capacity:
                section.capacity = standing_capacity
                update_fields.append("capacity")
            if update_fields:
                section.save(update_fields=update_fields)

            if sec_type == SectionType.SEATED:
                created_seats += self._ensure_seats_for_seated_section(section, rows, per_row)
            else:
                created_seats += self._ensure_synthetic_seats_for_standing(section, section.capacity)

        return venue, area, plan, created_seats

    def _ensure_seats_for_seated_section(self, section: Section, rows: int, per_row: int) -> int:
        """Tworzy brakujące siedzące Seat w formie Rząd(1..rows) × Miejsce(1..per_row)."""
        existing = set(
            Seat.objects.filter(section=section).values_list("row", "number")
        )
        to_create = []
        for r in range(1, rows + 1):
            for n in range(1, per_row + 1):
                key = (str(r), str(n))
                if key not in existing:
                    to_create.append(Seat(section=section, row=str(r), number=str(n)))
        Seat.objects.bulk_create(to_create, ignore_conflicts=True)
        return len(to_create)

    def _ensure_synthetic_seats_for_standing(self, section: Section, capacity: int) -> int:
        """Dla Płyty tworzymy „siedzenia” z rzędem S i numerami 1..capacity, aby EventSeat i UI działały bez zmian."""
        if capacity <= 0:
            return 0
        existing = set(
            Seat.objects.filter(section=section).values_list("row", "number")
        )
        to_create = []
        for i in range(1, capacity + 1):
            key = ("S", str(i))
            if key not in existing:
                to_create.append(Seat(section=section, row="S", number=str(i)))
        Seat.objects.bulk_create(to_create, ignore_conflicts=True)
        return len(to_create)

    def _upsert_event_with_layout(self, item: dict) -> Tuple[Event, bool, int, int]:
        """Tworzy/aktualizuje Event i pełny układ. Zwraca: (event, was_created, seats_created, eventseats_created)."""
        name = item["name"].strip()
        city = item["city"].strip()
        venue_name = item["venue"].strip()
        date_str = item["date"]
        time_str = item.get("time")
        dt = self._parse_datetime(date_str, time_str)

        venue, area, plan, seats_created = self._get_or_create_layout(venue_name, city)

        defaults = {
            "city": city,
            "venue": venue,
            "seating_plan": plan,
            "total_seats": item.get("total_seats") or 0,
            "available_seats": item.get("available_seats") or 0,
            "price": item.get("price") or 0,
            "description": item.get("description", ""),
            "highlights": item.get("highlights", []),
        }
        defaults["date"] = dt

        event, created = Event.objects.update_or_create(
            name=name,
            date=dt,
            defaults=defaults,
        )

        evseats_created = self._ensure_event_seats(event, plan)

        return event, created, seats_created, evseats_created

    def _ensure_event_seats(self, event: Event, plan: SeatingPlan) -> int:
        """Tworzy brakujące EventSeat dla wszystkich Seat w planie."""
        seats = Seat.objects.filter(section__plan=plan).values_list("id", flat=True)
        existing = set(
            EventSeat.objects.filter(event=event).values_list("seat_id", flat=True)
        )
        to_create = []
        for seat_id in seats:
            if seat_id not in existing:
                to_create.append(EventSeat(event=event, seat_id=seat_id, is_reserved=False))
        EventSeat.objects.bulk_create(to_create, ignore_conflicts=True)
        return len(to_create)
