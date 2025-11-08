from decimal import Decimal
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
from django.utils.encoding import smart_str
import os
import base64
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from .utils import render_ticket_pdf_to_content, default_storage, make_qr_code
from apps.events.models import Event, EventSeat
from .models import Booking, BookingItem
from .utils import generate_ticket_number
from pathlib import Path
from kulturalny_kod.logger import get_logger

logger = get_logger(__name__)

@login_required
def my_bookings(request):
    booking_items = (
        BookingItem.objects
        .filter(booking__user=request.user)
        .select_related("booking", "event", "seat__seat__section")
        .order_by("-booking__created_at")
    )
    return render(request, "my_bookings.html", {"booking_items": booking_items})

@require_http_methods(["GET", "POST"])
@login_required
def booking_view(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    raw_seats = (
        EventSeat.objects.filter(event=event, is_reserved=False)
        .select_related("seat__section")
        .order_by("seat__section__name", "seat__row", "seat__number")
    )

    seats = []
    for ev in raw_seats:
        section = ev.seat.section if ev.seat else ev.section
        row = ev.seat.row if ev.seat else None
        number = ev.seat.number if ev.seat else None
        modifier = section.price_modifier if section else Decimal(0)
        seat_price = event.price + modifier
        seats.append({
            "id": ev.id,
            "section": section.name if section else "",
            "row": row,
            "number": number,
            "price": seat_price,
            "is_seated": bool(ev.seat),
        })

    if request.method == "POST":
        seat_id = request.POST.get("seat_id")
        if not seat_id:
            messages.error(request, "Musisz wybrać miejsce.")
            return render(request, "booking_form.html", {"event": event, "seats": seats})

        try:
            with transaction.atomic():
                booking_id = request.session.get("booking_id")
                booking = None
                if booking_id:
                    try:
                        booking = Booking.objects.get(pk=int(booking_id), user=request.user)
                    except (Booking.DoesNotExist, ValueError, TypeError):
                        request.session.pop("booking_id", None)

                if booking is None:
                    booking = Booking.objects.create(
                        user=request.user,
                        email=request.user.email,
                        total_price=Decimal(0),
                    )
                    request.session["booking_id"] = booking.pk
                    request.session.modified = True

                evseat = EventSeat.objects.select_for_update().get(pk=int(seat_id), event=event)
                if evseat.is_reserved:
                    messages.warning(request, "To miejsce jest już zajęte.")
                    return redirect("events:event_detail", pk=event.pk)

                evseat.is_reserved = True
                evseat.save(update_fields=["is_reserved"])

                modifier = evseat.seat.section.price_modifier if evseat.seat else Decimal(0)
                seat_price = event.price + modifier

                BookingItem.objects.create(
                    booking=booking,
                    event=event,
                    full_name=request.user.get_full_name() or request.user.username,
                    quantity=1,
                    total_price=seat_price,
                    ticket_number=generate_ticket_number(),
                    seat=evseat if evseat.seat else None,
                    locked_at=timezone.now(),                )


                total = sum(i.total_price for i in booking.items.all())
                booking.total_price = total
                booking.save(update_fields=["total_price"])

        except Exception as e:
            messages.error(request, f"Nie udało się dodać miejsca: {e}")
            return render(request, "booking_form.html", {"event": event, "seats": seats})

        messages.success(request, "Dodano do koszyka.")
        return redirect("payments:cart")

    return render(request, "booking_form.html", {"event": event, "seats": seats})

@login_required
def booking_item_cancel(request, booking_item_id: int):
    item = get_object_or_404(BookingItem, pk=booking_item_id, booking__user=request.user)
    booking = item.booking

    if request.method == "POST":
        # zwolnij miejsce, jeśli było przypisane
        if item.seat_id:
            try:
                evseat = EventSeat.objects.get(pk=item.seat_id)
                evseat.is_reserved = False
                evseat.save(update_fields=["is_reserved"])
            except EventSeat.DoesNotExist:
                pass

        item.delete()

        new_total = sum(i.total_price for i in booking.items.all())
        booking.total_price = new_total
        booking.save(update_fields=["total_price"])

        if booking.items.count() == 0:
            request.session.pop("booking_id", None)
            request.session.modified = True

        messages.success(request, "Pozycja została anulowana.")
    else:
        messages.info(request, "Potwierdź anulowanie przyciskiem.")

    return redirect("booking:my_bookings")


@login_required
def ticket_pdf(request, booking_item_id: int):
    item = get_object_or_404(BookingItem, pk=booking_item_id, booking__user=request.user)
    event = item.event

    qr_content_file = make_qr_code(item.ticket_number)  # ContentFile
    qr_bytes = qr_content_file.read()
    qr_data_uri = "data:image/png;base64," + base64.b64encode(qr_bytes).decode("ascii")

    pdf_content = render_ticket_pdf_to_content(
        event=event,
        booking_item=item,
        qr_url=qr_data_uri,  # ← przekazujemy data URI, szablon pozostaje bez zmian
    )

    if not item.pdf_file:
        saved = default_storage.save(f"tickets/{item.ticket_number}.pdf", pdf_content)
        item.pdf_file.name = saved
        item.save(update_fields=["pdf_file"])

    pdf_bytes = pdf_content.read()
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{smart_str(item.ticket_number)}.pdf"'
    return resp
