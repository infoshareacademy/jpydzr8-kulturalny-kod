from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Booking, BookingItem
from apps.payments.models import Payment

EXPIRE_AFTER = timedelta(minutes=20)


def expire_stale_locks(event=None, user=None) -> None:
    """
    Anuluje koszykowe blokady starsze niż EXPIRE_AFTER:
      - ustawia Payment -> CANCELED (jeśli było CREATED/PENDING/AUTHORIZED),
      - usuwa BookingItem bez PDF (koszykowe) i zwalnia EventSeat,
      - usuwa puste Booking.
    Opcjonalnie zawężone do eventu i/lub użytkownika.
    """
    now = timezone.now()
    items = (
        BookingItem.objects
        .select_related("booking", "seat", "booking__payment")
        .filter(pdf_file__isnull=True, locked_at__lt=now - EXPIRE_AFTER)
    )

    if event:
        items = items.filter(event=event)
    if user:
        items = items.filter(booking__user=user)

    # grupowanie po booking_id
    grouped = {}
    for it in items:
        grouped.setdefault(it.booking_id, []).append(it)

    for booking_id, bucket in grouped.items():
        with transaction.atomic():
            booking = Booking.objects.select_related("payment").get(pk=booking_id)

            # 1) zaktualizuj ewentualny Payment
            p = getattr(booking, "payment", None)
            if p and p.status in (
                Payment.Status.CREATED,
                Payment.Status.PENDING,
                Payment.Status.AUTHORIZED,
            ):
                p.status = Payment.Status.CANCELED
                p.save(update_fields=["status", "updated_at"])

            # 2) zwolnij miejsca + usuń koszykowe pozycje
            for it in bucket:
                if it.seat:
                    it.seat.is_reserved = False
                    it.seat.save(update_fields=["is_reserved"])
                it.delete()

            # 3) jeśli pusto – usuń Booking
            if not booking.items.exists():
                booking.delete()
