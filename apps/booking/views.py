from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.events.models import Event
from .forms import BookingForm
from .models import Booking, BookingItem
from .utils import generate_ticket_number, make_qr_code, create_single_booking_item
from .services import (
    save_booking_to_csv,
    save_booking_to_json,
    render_ticket_pdf_to_content,
)
from kulturalny_kod.logger import get_logger
logger = get_logger(__name__)


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
                logger.info(f"Niewystarczająca ilość miejsc przy próbie zamówienia na {event.name} -> wymagana liczba: {quantity}, dostępna: {event.available_seats}.")
                return render(request, 'booking_form.html', {'event': event, 'form': form})

            ticket_no = generate_ticket_number()

            full_name = f"{request.user.first_name} {request.user.last_name}".strip()
            if not full_name:
                full_name = request.user.username

                if quantity > event.available_seats:
                    form.add_error('quantity', 'Brak wystarczającej liczby wolnych miejsc.')
                    logger.info(f"Niewystarczająca ilość miejsc przy próbie zamówienia na {event.name} -> wymagana liczba: {quantity}, dostępna: {event.available_seats}.")
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
            logger.info(
                f"Utworzono rezerwację: "
                f"[ticket_no={ticket_no}] "
                f"[user={request.user.username} ({request.user.email})] "
                f"[event={event.name}] "
                f"[quantity={quantity}] "
                f"[total_price={total:.2f}] "
                f"[ticket_number={ticket_no}]"
            )

            event.available_seats = event.available_seats - quantity
            event.save(update_fields=['available_seats'])

            qr_content = f'{ticket_no}|event:{event.pk}|email:{booking.email}'
            qr_file = make_qr_code(qr_content)
            qr_path = f"tickets/{ticket_no}_qr.png"
            qr_saved_path = default_storage.save(qr_path, qr_file)

            qr_abs_path = Path(default_storage.path(qr_saved_path)).resolve()
            qr_url = qr_abs_path.as_uri()

            pdf_content = render_ticket_pdf_to_content(
                event=event,
                booking_item=booking,
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
    booking_items = BookingItem.objects.filter(booking__user=request.user).order_by('-booking__created_at')
    # bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_bookings.html', {'booking_items': booking_items})


@login_required
def booking_view(request: HttpRequest, event_id: int) -> HttpResponse:
    event = get_object_or_404(Event, pk=event_id)
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            cart = request.session.get('cart', {})
            cart[str(event_id)] = cart.get(str(event_id), 0) + quantity
            request.session['cart'] = cart
            logger.info(f"Dodano do koszyka: event_id={event_id}, quantity={quantity}, user={request.user.username}")
            return redirect('payments:cart')
    else:
        form = BookingForm()
    
    return render(request, 'booking_form.html', {'event': event, 'form': form})


@require_http_methods(['POST'])
@login_required
def cart_checkout(request: HttpRequest) -> HttpResponse:
    user = getattr(request, "user")
    cart = request.session.get('cart', {})
    if not cart:
        return HttpResponseBadRequest("Koszyk jest pusty")

    total_price = Decimal(0)
    
    try:
        with transaction.atomic():
            booking = Booking.objects.create(
                user=user,
                email=user.email,
                total_price=total_price,
            )
            for event_id, quantity in cart.items():
                result = create_single_booking_item(
                    booking=booking,
                    user=user,
                    event_id=int(event_id),
                    quantity=quantity
                )
                if not result:
                    raise Exception(event_id)
                
                total_price += result
            # Update booking with total price
            booking.total_price = total_price
            booking.save(update_fields=['total_price'])
                
        
        #clear cart
        request.session['cart'] = {}
        request.session.modified = True
        return redirect('booking:success_multiple', booking_number = booking.pk)

    except Exception as e:
        # If anything fails, all bookings are rolled back automatically
        print("Failed to create bookings:", e)
        return HttpResponseBadRequest("Nie udało się zrealizować rezerwacji. Spróbuj ponownie.")

    payment = Payment.objects.create(
        amount=total_price,
        currency="PLN",
        description="Opis płatności",
        payer_email=request.user.email,
        metadata={"cart": cart}
    )

    return redirect(reverse('payments:start_payment', kwargs={'pk': payment.pk}))


@login_required
def booking_success_multiple(request, booking_number):
    booking = get_object_or_404(Booking, pk=booking_number, user=request.user)
    return render(request, 'booking_success_multiple.html', {'items': booking.items.all()})


@require_http_methods(["POST"])
@login_required
def booking_item_cancel(request, booking_item_id: int):
    booking_item = get_object_or_404(BookingItem, pk=booking_item_id, booking__user=request.user)
    if booking_item.booking.user != request.user:
        return HttpResponseBadRequest("Nie jesteś właścicielem tego zamówienia.")
    if request.method == "POST":
        booking_item.delete()
        messages.success(request, f"Rezerwacja '{booking_item.event.name}' została anulowana.")
        logger.info(f"Anulowano rezerwację: [booking_item_id={booking_item_id}, user={request.user.username}]")
        return redirect('booking:my_bookings')
    return redirect('booking:my_bookings')

