import csv, json, io
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.core.files.base import ContentFile

from weasyprint import HTML, CSS

# Katalog archiwum CSV/JSON (pozostaje w apps/booking/media/bookings)
ARCHIVE_DIR = Path(settings.BASE_DIR) / 'apps' / 'booking' / 'media' / 'bookings'
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def save_booking_to_csv(booking, booking_item):
    csv_path = ARCHIVE_DIR / 'bookings.csv'
    new_file = not csv_path.exists()

    with csv_path.open('a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow([
                'ticket_number', 'event_id', 'event', 'user_id', 'username',
                'full_name', 'email', 'quantity', 'total_price', 'created_at'
            ])
        writer.writerow([
            booking_item.ticket_number,
            booking_item.event_id,
            getattr(booking_item.event, 'title', getattr(booking_item.event, 'name', 'event')),
            booking.user.id if booking.user else '',
            booking.user.username if booking.user else '',
            booking_item.full_name,
            booking.email,
            booking_item.quantity,
            str(booking_item.total_price),
            booking.created_at.isoformat()
        ])


def save_booking_to_json(booking, booking_item):
    json_path = ARCHIVE_DIR / 'bookings.json'
    data = []
    if json_path.exists():
        data = json.loads(json_path.read_text(encoding='utf-8'))

    data.append({
        'ticket_number': booking_item.ticket_number,
        'event_id': booking_item.event_id,
        'event': getattr(booking_item.event, 'title', getattr(booking_item.event, 'name', 'event')),
        'user_id': booking.user.id if booking.user else None,
        'username': booking.user.username if booking.user else None,
        'full_name': booking_item.full_name,
        'email': booking.email,
        'quantity': booking_item.quantity,
        'total_price': str(booking_item.total_price),
        'created_at': booking.created_at.isoformat(),
    })

    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def render_ticket_pdf_to_content(event, booking_item, qr_url: str) -> ContentFile:
    """
    Renderuje PDF z zewnętrznym CSS i absolutnym file:// do obrazu QR.
    """
    html = render_to_string('ticket_pdf.html', {
        'event': event,
        'booking_item': booking_item,
        'qr_url': qr_url,
    })
    pdf_io = io.BytesIO()
    css_file = finders.find('booking/css/ticket.css')

    HTML(string=html, base_url=settings.MEDIA_ROOT).write_pdf(
        pdf_io,
        stylesheets=[CSS(css_file)] if css_file else None
    )
    return ContentFile(pdf_io.getvalue(), name=f'{booking_item.ticket_number}.pdf')