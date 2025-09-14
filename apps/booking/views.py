from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
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
@login_required
def booking_create(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            price = _event_price(event)
            total = price * quantity

            if quantity > event.available_seats:
                form.add_error('quantity', 'Brak wystarczającej liczby wolnych miejsc.')
                return render(request, 'booking_form.html', {'event': event, 'form': form})

            ticket_no = generate_ticket_number()

            full_name = f"{request.user.first_name} {request.user.last_name}".strip()
            if not full_name:
                full_name = request.user.username

                if quantity > event.available_seats:
                    form.add_error('quantity', 'Brak wystarczającej liczby wolnych miejsc.')
                    return render(request, 'booking_form.html', {'event': event, 'form': form})

            booking = Booking.objects.create(
                event=event,
                user=request.user,
                full_name=full_name,
                email=request.user.email,
                quantity=quantity,
                total_price=total,
                ticket_number=ticket_no,
            )

            event.available_seats = event.available_seats - quantity
            event.save(update_fields=['available_seats'])

            qr_content = f'{ticket_no}|event:{event.id}|email:{booking.email}'
            qr_file = make_qr_code(qr_content)
            qr_path = f"tickets/{ticket_no}_qr.png"
            qr_saved_path = default_storage.save(qr_path, qr_file)

            qr_abs_path = Path(default_storage.path(qr_saved_path)).resolve()
            qr_url = qr_abs_path.as_uri()

            pdf_content = render_ticket_pdf_to_content(
                event=event,
                booking=booking,
                qr_url=qr_url
            )

            pdf_path = f"tickets/{ticket_no}.pdf"
            pdf_saved_path = default_storage.save(pdf_path, pdf_content)

            booking.pdf_file.name = pdf_saved_path
            booking.save(update_fields=['pdf_file'])

            save_booking_to_csv(booking)
            save_booking_to_json(booking)

            return redirect(reverse('booking:success', kwargs={'ticket_number': ticket_no}))
    else:
        form = BookingForm()

    return render(request, 'booking_form.html', {'event': event, 'form': form})


@login_required
def booking_success(request, ticket_number):
    booking = get_object_or_404(Booking, ticket_number=ticket_number, user=request.user)
    return render(request, 'booking_success.html', {'booking': booking})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_bookings.html', {'bookings': bookings})
