from decimal import Decimal
import io
import qrcode
import base64
from pathlib import Path
import os
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files import File
from django.shortcuts import get_object_or_404
from django.conf import settings

from .models import Booking, BookingItem
from .services import save_booking_to_csv, save_booking_to_json
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
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

def make_qr_data_url(data: str) -> str:
    img_file = make_qr_code(data)  # make_qr_code zwraca ContentFile("qr.png")
    img_file.seek(0)               # ADDED: dla pewności, czytamy od początku
    b64 = base64.b64encode(img_file.read()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def reserve_event_slots_on_purchase(event: Event, quantity: int) -> None:
    event.available_seats = max(event.available_seats - quantity, 0)
    event.save(update_fields=["available_seats"])


def release_event_slots(event: Event, quantity: int) -> None:
    event.available_seats = event.available_seats + quantity
    event.save(update_fields=["available_seats"])


def create_single_booking_item(
    booking: Booking, user: User, event_id: int, quantity: int
) -> bool | Decimal:

    logger.info(
        f"Proba zamówienia na {event_id} przez {user.username} ({user.email}) -> liczba miejsc: {quantity}"
    )

    if not user.is_authenticated:
        logger.info("Nieudana próba zamówienia bez zalogowania.")
        return False

    event = get_object_or_404(Event, pk=event_id)

    # UWAGA: warunek dostępności w nowym flow powinien bazować na EventSeat,
    # a nie na event.available_seats. Ten check zostawiamy jako miękki strażnik.
    if quantity > event.available_seats:
        logger.info(
            f"Niewystarczająca liczba miejsc dla {event.name}: "
            f"żądano {quantity}, dostępne {event.available_seats}."
        )
        return False

    total_price = event.price * quantity

    ticket_no = generate_ticket_number()
    full_name = f"{user.first_name} {user.last_name}".strip() or user.username

    booking_item = BookingItem.objects.create(
        booking=booking,
        event=event,
        full_name=full_name,
        quantity=quantity,
        total_price=total_price,
        ticket_number=ticket_no,
    )

    logger.info(
        "Utworzono rezerwację: "
        f"[ticket_no={ticket_no}] "
        f"[user={user.username} ({user.email})] "
        f"[event={event.name}] "
        f"[quantity={quantity}] "
        f"[total_price={total_price:.2f}]"
    )

    # REMOVED: generowanie QR + PDF + zapis pliku (robimy po SUCCEEDED albo on-demand w ticket_pdf)
    # REMOVED: dołączanie plików do maila tutaj

    # OPTIONAL: jeśli te exporty są nadal potrzebne – zostaw
    try:
        save_booking_to_csv(booking, booking_item)
        save_booking_to_json(booking, booking_item)
    except Exception as e:
        logger.warning(f"Zapis booking CSV/JSON nie powiódł się: {e}")

    return total_price


def send_booking_confirmation_email(booking: Booking):
    user = booking.user

    message = render_to_string(
        "emails/booking_confirmation.html",
        {"user": user, "booking": booking},
    )

    email = EmailMessage(
        subject=f"Potwierdzenie rezerwacji — #{booking.id}",
        body=message,
        to=[user.email],
    )
    email.content_subtype = "html"

    for item in booking.items.all():
        pdf_name = item.pdf_file.name

        if not pdf_name:
            continue

        if default_storage.exists(pdf_name):
            with default_storage.open(pdf_name, "rb") as f:
                email.attach(
                    filename=os.path.basename(pdf_name),
                    content=f.read(),
                    mimetype="application/pdf",
                )
        else:
            print("PDF NOT FOUND:", pdf_name)

    for item in booking.items.all():
        print("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")
        print("PDF FIELD NAME:", item.pdf_file.name)
        try:
            print("PDF PATH:", item.pdf_file.path)
        except Exception as e:
            print("ERROR item.pdf_file.path:", e)

        print("STORAGE EXISTS?:", default_storage.exists(item.pdf_file.name))
        abs_path = os.path.join(settings.MEDIA_ROOT, item.pdf_file.name)
        print("ABS PATH:", abs_path)
        print("EXISTS ON DISK?:", os.path.exists(abs_path))
        print("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")

    email.send()
