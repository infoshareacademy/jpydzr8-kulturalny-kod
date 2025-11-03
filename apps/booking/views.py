from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.conf import settings
from apps.events.models import (
    Event,
    EventSeat
)
from .forms import BookingForm
from .models import (
    Booking,
    BookingItem
)
from .utils import (
    generate_ticket_number,
    render_ticket_pdf_to_content,
    default_storage, make_qr_code,
    send_booking_confirmation_email
)
from kulturalny_kod.logger import get_logger

import os
logger = get_logger(__name__)


def _event_price(event):
    return Decimal(getattr(event, "price", "0"))


@login_required
def booking_success(request, ticket_number):
    booking = get_object_or_404(Booking, ticket_number=ticket_number, user=request.user)
    return render(request, "booking_success.html", {"booking": booking})


@login_required
def my_bookings(request):
    booking_items = BookingItem.objects.filter(booking__user=request.user).order_by(
        "-booking__created_at"
    )
    return render(request, "my_bookings.html", {"booking_items": booking_items})


@require_http_methods(["GET", "POST"])
@login_required
def booking_view(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    cart = request.session.get("cart", {})

    raw_seats = (
        EventSeat.objects.filter(event=event, is_reserved=False)
        .select_related("seat__section")
        .order_by("seat__section__name", "seat__row", "seat__number")
    )

    seats = []
    for ev in raw_seats:
        if ev.seat:
            section = ev.seat.section
            row = ev.seat.row
            number = ev.seat.number
        else:
            section = ev.section
            row = None
            number = None
        seat_price = event.price + section.price_modifier

        seats.append({
            "id": ev.id,
            "section": section.name,
            "row": ev.seat.row if ev.seat else None,
            "number": ev.seat.number if ev.seat else None,
            "price": seat_price,
            "is_seated": bool(ev.seat),
        })

    if request.method == "POST":
        form = BookingForm(request.POST)
        seat_id = request.POST.get("seat_id")

        if not seat_id:
            messages.error(request, "Musisz wybrać miejsce.")
            return render(request, "booking_form.html", {
                "event": event, "form": form, "seats": seats
            })

        if form.is_valid():
            if str(event_id) in cart and int(seat_id) in cart[str(event_id)]:
                messages.warning(request, "To miejsce jest już w Twoim koszyku.")
                return redirect("payments:cart")

            cart.setdefault(str(event_id), [])
            cart[str(event_id)].append(int(seat_id))
            request.session["cart"] = cart
            request.session.modified = True

            messages.success(request, "Miejsce dodane do koszyka")
            return redirect("payments:cart")

    else:
        form = BookingForm()

    return render(request, "booking_form.html", {
        "event": event,
        "form": form,
        "seats": seats,
    })



@require_http_methods(["POST"])
@login_required
def cart_checkout(request: HttpRequest) -> HttpResponse:
    user = request.user
    cart = request.session.get("cart", {})
    if not cart:
        return HttpResponseBadRequest("Koszyk jest pusty")

    total_price = Decimal(0)

    try:
        with transaction.atomic():
            booking = Booking.objects.create(
                user=user,
                email=user.email,
                total_price=0,
            )

            for event_id, seat_ids in cart.items():
                event = Event.objects.get(pk=int(event_id))

                for seat_id in seat_ids:
                    evseat = EventSeat.objects.select_for_update().get(pk=seat_id)

                    if evseat.is_reserved:
                        raise Exception(f"Miejsce {seat_id} już zajęte")

                    evseat.is_reserved = True
                    evseat.save(update_fields=["is_reserved"])

                    if evseat.seat:
                        section_modifier = evseat.seat.section.price_modifier
                    else:
                        section_modifier = Decimal(0)

                    seat_price = event.price + section_modifier

                    booking_item = BookingItem.objects.create(
                        booking=booking,
                        event=event,
                        full_name=user.get_full_name() or user.username,
                        quantity=1,
                        total_price=seat_price,
                        ticket_number=generate_ticket_number(),
                        seat=evseat if evseat.seat else None,
                    )

                    total_price += seat_price

                    qr_content = make_qr_code(booking_item.ticket_number)
                    qr_path = f"qr_codes/{booking_item.ticket_number}.png"
                    qr_saved_path = default_storage.save(qr_path, qr_content)
                    qr_url = os.path.join(settings.MEDIA_URL, qr_saved_path)

                    pdf_content = render_ticket_pdf_to_content(
                        event=event,
                        booking_item=booking_item,
                        qr_url=qr_url,
                    )

                    pdf_path = f"tickets/{booking_item.ticket_number}.pdf"
                    pdf_saved_path = default_storage.save(pdf_path, pdf_content)

                    booking_item.pdf_file.name = pdf_saved_path
                    booking_item.save(update_fields=["pdf_file"])

            booking.total_price = total_price
            booking.save(update_fields=["total_price"])

        send_booking_confirmation_email(booking)

        request.session["cart"] = {}
        request.session.modified = True

        return redirect("booking:success_multiple", booking_number=booking.pk)

    except Exception as e:
        print("Failed to create bookings:", e)
        return HttpResponseBadRequest("Nie udało się zrealizować rezerwacji.")



@login_required
def booking_success_multiple(request, booking_number):
    booking = get_object_or_404(Booking, pk=booking_number, user=request.user)
    return render(
        request, "booking_success_multiple.html", {"items": booking.items.all()}
    )


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

