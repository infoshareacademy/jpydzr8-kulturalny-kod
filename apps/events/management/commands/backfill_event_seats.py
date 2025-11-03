from django.core.management.base import BaseCommand
from apps.events.models import Event, EventSeat
from apps.venues.models import SectionType


class Command(BaseCommand):
    help = "Generate EventSeat for seated and standing sections"

    def handle(self, *args, **options):
        created = 0

        for event in Event.objects.select_related("seating_plan"):
            plan = event.seating_plan
            if not plan:
                continue

            for section in plan.sections.all():

                if section.type == SectionType.STANDING:
                    for i in range(1, section.capacity + 1):
                        _, was_created = EventSeat.objects.get_or_create(
                            event=event,
                            section=section,
                            seat=None,
                            defaults={"is_reserved": False},
                        )
                        created += was_created
                    continue

                for seat in section.seats.all():
                    _, was_created = EventSeat.objects.get_or_create(
                        event=event,
                        section=section,
                        seat=seat,
                        defaults={"is_reserved": False},
                    )
                    created += was_created

        self.stdout.write(
            self.style.SUCCESS(f"Created {created} EventSeat records")
        )
