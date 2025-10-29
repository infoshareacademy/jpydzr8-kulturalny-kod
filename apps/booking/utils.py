from decimal import Decimal
import io
import qrcode
from pathlib import Path
from typing import Tuple

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files import File
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect

from .models import Booking, BookingItem
from .services import (
    save_booking_to_csv,
    save_booking_to_json,
    render_ticket_pdf_to_content,
)
from apps.events.models import Event
from kulturalny_kod.logger import get_logger

logger = get_logger(__name__)


def generate_ticket_number(prefix="TKT"):
    from uuid import uuid4

    return f"{prefix}-{uuid4().hex[:10].upper()}"


def make_qr_code(data: str) -> ContentFile:
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return ContentFile(buf.getvalue(), name="qr.png")


def create_single_booking_item(
    booking: Booking, user: User, event_id: int, quantity: int
) -> bool | Decimal:
    """
    Create a single booking for a user and an event.
    Returns True if booking was created, False otherwise.
    """
    logger.info(
        f"Proba zamówienia na {event_id} przez {user.username} ({user.email}) -> liczba miejsc: {quantity}"
    )
    # Generate Booking instance
    if not user.is_authenticated:
        logger.info(f"Nieudana próba zamówienia bez zalogowania.")
        return False
    event = get_object_or_404(Event, pk=event_id)
    if quantity > event.available_seats:
        logger.info(
            f"Niewystarczająca ilość miejsc przy próbie zamówienia na {event.name} -> wymagana liczba: {quantity}, dostępna: {event.available_seats}."
        )
        return False

    total_price = event.price * quantity
    ticket_no = generate_ticket_number()
    full_name = f"{user.first_name} {user.last_name}".strip()
    if not full_name:
        full_name = user.username

    booking_item = BookingItem.objects.create(
        booking=booking,
        event=event,
        full_name=full_name,
        quantity=quantity,
        total_price=total_price,
        ticket_number=ticket_no,
    )
    logger.info(
        f"Utworzono rezerwację: "
        f"[ticket_no={ticket_no}] "
        f"[user={user.username} ({user.email})] "
        f"[event={event.name}] "
        f"[quantity={quantity}] "
        f"[total_price={total_price:.2f}] "
        f"[ticket_number={ticket_no}]"
    )

    # Update event with available seats info
    event.available_seats = event.available_seats - quantity
    event.save(update_fields=["available_seats"])

    # Generate QR code
    qr_content = f"{ticket_no}|event:{event.pk}|email:{user.email}"
    qr_file = make_qr_code(qr_content)
    qr_path = f"tickets/{ticket_no}_qr.png"
    qr_saved_path = default_storage.save(qr_path, qr_file)

    qr_abs_path = Path(default_storage.path(qr_saved_path)).resolve()
    qr_url = qr_abs_path.as_uri()

    pdf_content = render_ticket_pdf_to_content(
        event=event, booking_item=booking_item, qr_url=qr_url
    )

    pdf_path = f"tickets/{ticket_no}.pdf"
    pdf_saved_path = default_storage.save(pdf_path, pdf_content)

    # 3. Attach PDF to booking
    with default_storage.open(pdf_saved_path, "rb") as f:
        booking_item.pdf_file.save(f"{ticket_no}.pdf", File(f), save=True)

    save_booking_to_csv(booking, booking_item)
    save_booking_to_json(booking, booking_item)
    return total_price
