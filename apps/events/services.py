from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.events.models import EventSeat
from apps.booking.models import BookingItem, TicketSeat


def reserve_seats_for_booking_item(
    booking_item: BookingItem, event_seat_ids: list[int]
):
    with transaction.atomic():
        seats = EventSeat.objects.select_for_update().filter(
            id__in=event_seat_ids, event=booking_item.event
        )

        if seats.count() != len(event_seat_ids):
            raise ValidationError("Niektóre miejsca nie istnieją dla tego wydarzenia.")

        for s in seats:
            if s.is_reserved or hasattr(s, "ticket_seat"):
                raise ValidationError(f"Miejsce {s.seat} jest już zajęte.")

        for s in seats:
            s.is_reserved = True
            s.reserved_at = timezone.now()
            s.save(update_fields=["is_reserved", "reserved_at"])
            TicketSeat.objects.create(booking_item=booking_item, event_seat=s)
