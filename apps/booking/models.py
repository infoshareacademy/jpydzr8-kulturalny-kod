from django.conf import settings
from django.db import models

from apps.events.models import Event, EventSeat
from apps.payments.models import Payment

class Booking(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    email = models.EmailField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f'Zamówienie użytkownika {getattr(self.user, "username", "Anonymous")} o numerze {self.pk} z {self.created_at} o wartości {self.total_price}'

    @property
    def payment_obj(self):
        # bezpieczny dostęp: gdy brak płatności -> None
        return getattr(self, "payment", None)

    @property
    def is_paid(self) -> bool:
        p = self.payment_obj
        return bool(p and p.status == Payment.Status.SUCCEEDED)

    @property
    def is_pending(self) -> bool:
        p = self.payment_obj
        return bool(p and p.status in {Payment.Status.PENDING, Payment.Status.AUTHORIZED})

    @property
    def is_unpaid(self) -> bool:
        p = self.payment_obj
        return (p is None) or p.status in {
            Payment.Status.CREATED, Payment.Status.FAILED, Payment.Status.CANCELED
        }

    @property
    def can_print_ticket(self) -> bool:
        # bilet/PDF dopiero po sukcesie
        return self.is_paid

    @property
    def can_pay_now(self) -> bool:
        # przycisk "Zapłać teraz"
        return self.is_unpaid

class BookingItem(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="items")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="items")
    full_name = models.CharField(max_length=120)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    ticket_number = models.CharField(max_length=32, unique=True)
    pdf_file = models.FileField(upload_to="tickets/", null=True, blank=True)
    seat = models.ForeignKey(
        EventSeat,
        on_delete=models.PROTECT,
        related_name="booking_items",
        null=True,
        blank=True,
        verbose_name="Zarezerwowane miejsce",
    )
    locked_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_canceled = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.ticket_number} - {self.full_name}"


class TicketSeat(models.Model):
    booking_item = models.ForeignKey(
        "booking.BookingItem", on_delete=models.CASCADE, related_name="ticket_seats"
    )
    event_seat = models.OneToOneField(
        "events.EventSeat", on_delete=models.PROTECT, related_name="ticket_seat"
    )

    def __str__(self):
        return f"{self.booking_item.ticket_number} → {self.event_seat.seat}"
