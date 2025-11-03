from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.venues.models import Seat
from .models import Event, EventSeat


@receiver(post_save, sender=Event)
def create_event_seats(sender, instance, created, **kwargs):
    if not created:
        return
    seats = Seat.objects.filter(section__plan=instance.seating_plan).values_list(
        "id", flat=True
    )
    EventSeat.objects.bulk_create(
        [EventSeat(event=instance, seat_id=sid) for sid in seats],
        ignore_conflicts=True,
    )
