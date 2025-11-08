import io
import qrcode

from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from .models import Booking
from kulturalny_kod.logger import get_logger

logger = get_logger(__name__)


def generate_ticket_number(prefix: str = "TKT") -> str:
    """Generuje krótki, unikalny numer biletu."""
    from uuid import uuid4
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def make_qr_code(data: str) -> ContentFile:
    """Zwraca ContentFile z obrazem PNG QR w pamięci (bez zapisu na dysk)."""
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return ContentFile(buf.getvalue(), name="qr.png")


def send_booking_confirmation_email(booking: Booking) -> None:
    """Wysyła e-mail z załączonymi wygenerowanymi PDF-ami (o ile są)."""
    user = booking.user

    message = render_to_string(
        "emails/booking_confirmation.html",
        {
            "user": user,
            "booking": booking,
        },
    )

    email = EmailMessage(
        subject="Potwierdzenie rezerwacji",
        body=message,
        to=[user.email],
    )
    email.content_subtype = "html"

    for item in booking.items.all():
        if item.pdf_file:
            try:
                email.attach_file(item.pdf_file.path)
            except Exception as exc:
                logger.warning(f"Nie udało się dołączyć PDF dla item_id={item.id}: {exc}")

    email.send()
