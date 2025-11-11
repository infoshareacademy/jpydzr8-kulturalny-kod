from django.db import transaction
from .models import Payment

def get_or_prepare_payment_for_booking(booking) -> Payment:
    """
    Zwraca Payment przypięty do Booking. Jeśli nie istnieje – tworzy.
    Jeśli wcześniejsza próba się nie udała, pozwala na retry tym samym rekordem.
    """
    with transaction.atomic():
        payment, created = Payment.objects.select_for_update().get_or_create(
            booking=booking,
            defaults=dict(
                amount=booking.total_price,
                currency="PLN",
                status=Payment.Status.CREATED,
                payer_email=getattr(booking.user, "email", "") or booking.email,
                metadata={"booking_id": booking.id},  # ewentualny snapshot
            ),
        )

        # Jeśli Payment zakończony nie-sukcesem i chcesz pozwolić na retry:
        if payment.is_final and payment.status != Payment.Status.SUCCEEDED:
            payment.status = Payment.Status.CREATED
            payment.external_id = None
            payment.save(update_fields=["status", "external_id"])

        return payment
