from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.events.models import Event
from .forms import BookingForm
from .models import Booking
from .utils import generate_ticket_number, make_qr_code
from .services import (
    save_booking_to_csv,
    save_booking_to_json,
    render_ticket_pdf_to_content,
)


def _event_price(event):
    return Decimal(getattr(event, 'price', '0'))


@require_http_methods(['GET', 'POST'])
def booking_create(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            price = _event_price(event)
            total = price * quantity

            ticket_no = generate_ticket_number()

            # 1) utworzenie rezerwacji
            booking = Booking.objects.create(
                event=event,
                user=request.user if request.user.is_authenticated else None,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                quantity=quantity,
                total_price=total,
                ticket_number=ticket_no,
            )

            # 2) QR -> zapis do /tickets
            qr_content = f'{ticket_no}|event:{event.id}|email:{booking.email}'
            qr_file = make_qr_code(qr_content)
            qr_path_rel = f"tickets/{ticket_no}_qr.png"
            default_storage.save(qr_path_rel, qr_file)

            # absolutny URL plikowy (WeasyPrint)
            qr_abs = Path(settings.MEDIA_ROOT) / qr_path_rel
            qr_url = f"file://{qr_abs.resolve()}"

            # 3) CSS i base_url
            base_url = request.build_absolute_uri('/')  # http://127.0.0.1:8000/
            css_url = request.build_absolute_uri('/static/booking/css/ticket.css')

            # 4) PDF - zapis do /tickets
            pdf_content = render_ticket_pdf_to_content(
                event=event,
                booking=booking,
                qr_url=qr_url,
                base_url=base_url,
                css_url=css_url,
            )
            pdf_path = default_storage.save(f"tickets/{ticket_no}.pdf", pdf_content)
            booking.pdf_file.name = pdf_path
            booking.save(update_fields=['pdf_file'])

            # 5) Archiwum
            save_booking_to_csv(booking)
            save_booking_to_json(booking)

            # 6) sukces
            return redirect(reverse('booking:success', kwargs={'ticket_number': ticket_no}))
    else:
        form = BookingForm()

    return render(request, 'booking_form.html', {'event': event, 'form': form})


def booking_success(request, ticket_number):
    booking = get_object_or_404(Booking, ticket_number=ticket_number)
    return render(request, 'booking_success.html', {'booking': booking})
