from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpRequest, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from apps.booking.utils_expire import expire_stale_locks
from apps.events.models import Event, EventSeat
from apps.payments.models import Payment
from .forms import BookingForm
from .models import Booking, BookingItem
from .utils import generate_ticket_number  # ← dodać, bo używasz w create

from kulturalny_kod.logger import get_logger

logger = get_logger(__name__)


def _event_price(event):
    return Decimal(getattr(event, "price", "0"))


@login_required
def booking_success(request, ticket_number):
    item = get_object_or_404(
        BookingItem.objects.select_related("booking"),
        ticket_number=ticket_number,
        booking__user=request.user
    )
    return render(request, "booking_success.html", {"booking_item": item})


@login_required
def my_bookings(request):
    expire_stale_locks(user=request.user)
    tab = request.GET.get("status", "all")

    qs = (
        BookingItem.objects
        .filter(booking__user=request.user)
        .select_related("booking", "booking__payment", "event")
        .order_by("-booking__created_at")
    )

    if tab == "paid":
        qs = qs.filter(
            is_canceled=False,
            booking__payment__status=Payment.Status.SUCCEEDED
        )

    elif tab == "unpaid":
        # nieopłacone = brak płatności lub payment w stanie „niefinalnym” (CREATED/PENDING/AUTHORIZED)
        qs = qs.filter(
            is_canceled=False
        ).filter(
            Q(booking__payment__isnull=True) |
            Q(booking__payment__status__in=[
                Payment.Status.CREATED,
                Payment.Status.PENDING,
                Payment.Status.AUTHORIZED,
            ])
        )

    elif tab == "canceled":
        # anulowane = pozycja oznaczona jako anulowana lub payment canceled/failed
        qs = qs.filter(
            Q(is_canceled=True) |
            Q(booking__payment__status__in=[
                Payment.Status.CANCELED,
                Payment.Status.FAILED,
            ])
        )

    # „all” = nic nie filtrujemy dodatkowo
    return render(request, "my_bookings.html", {"booking_items": qs, "status": tab})


@require_http_methods(["GET", "POST"])
@login_required
def booking_view(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    expire_stale_locks(event=event, user=request.user)

    raw_seats = (
        EventSeat.objects.filter(event=event, is_reserved=False)
        .select_related("seat__section")
        .order_by("seat__section__name", "seat__row", "seat__number")
    )

    seats = []
    for ev in raw_seats:
        if ev.seat:
            section = ev.seat.section
        else:
            section = ev.section
        seat_price = (event.price or Decimal(0)) + (section.price_modifier or Decimal(0))

        seats.append(
            {
                "id": ev.id,
                "section": section.name,
                "row": ev.seat.row if ev.seat else None,
                "number": ev.seat.number if ev.seat else None,
                "price": seat_price,
                "is_seated": bool(ev.seat),
            }
        )

    if request.method == "POST":
        form = BookingForm(request.POST)
        seat_id = request.POST.get("seat_id")

        if not seat_id:
            messages.error(request, _("Musisz wybrać miejsce."))
            return render(request, "booking_form.html", {"event": event, "form": form, "seats": seats})

        if not form.is_valid():
            return render(request, "booking_form.html", {"event": event, "form": form, "seats": seats})

        # jeden „otwarty” booking w sesji = koszyk
        booking_id = request.session.get("pay_booking_id")
        booking = Booking.objects.filter(pk=booking_id, user=request.user).first() if booking_id else None

        if not booking:
            booking = Booking.objects.create(
                user=request.user,
                email=request.user.email,
                total_price=Decimal(0),
            )
            request.session["pay_booking_id"] = booking.id
            request.session.modified = True

        with transaction.atomic():
            evseat = EventSeat.objects.select_for_update().get(pk=int(seat_id))
            if evseat.is_reserved:
                messages.warning(request, _("To miejsce jest już zajęte."))
                return redirect("events:event_detail", pk=event.id)

            evseat.is_reserved = True
            evseat.save(update_fields=["is_reserved"])

            section_modifier = (evseat.seat.section.price_modifier if evseat.seat else Decimal(0)) or Decimal(0)
            seat_price = (event.price or Decimal(0)) + section_modifier

            BookingItem.objects.create(
                booking=booking,
                event=event,
                full_name=request.user.get_full_name() or request.user.username,
                quantity=1,
                total_price=seat_price,
                ticket_number=generate_ticket_number(),
                seat=evseat if evseat.seat else None,
                pdf_file=None,  # PDF dopiero po opłaceniu
            )

            # suma tylko z aktywnych (nieanulowanych)
            total = booking.items.filter(is_canceled=False).aggregate(sum=Sum("total_price"))["sum"] or Decimal(0)
            booking.total_price = total
            booking.save(update_fields=["total_price"])

        messages.success(request, _("Dodano do koszyka."))
        return redirect("payments:cart")

    # GET
    form = BookingForm()
    return render(request, "booking_form.html", {"event": event, "form": form, "seats": seats})


@login_required
def booking_success_multiple(request, booking_number):
    expire_stale_locks(user=request.user)
    booking = get_object_or_404(Booking, pk=booking_number, user=request.user)
    return render(
        request, "booking_success_multiple.html", {"items": booking.items.all()}
    )


@require_http_methods(["POST"])
@login_required
def booking_item_cancel(request, booking_item_id: int):
    item = get_object_or_404(
        BookingItem.objects.select_related("booking", "booking__payment", "seat"),
        pk=booking_item_id,
        booking__user=request.user
    )

    # bezpieczeństwo
    if item.booking.user_id != request.user.id:
        return HttpResponseBadRequest(_("Nie jesteś właścicielem tego zamówienia."))

    # jeśli już anulowane – nic nie rób
    if item.is_canceled:
        messages.info(request, _("Ta pozycja jest już anulowana."))
        return redirect("booking:my_bookings")

    # oznacz jako anulowane + zwolnij miejsce
    item.is_canceled = True
    item.canceled_at = timezone.now()
    item.save(update_fields=["is_canceled", "canceled_at"])

    if item.seat:
        seat = item.seat
        seat.is_reserved = False
        seat.save(update_fields=["is_reserved"])

    # przelicz total po aktywnych
    booking = item.booking
    new_total = booking.items.filter(is_canceled=False).aggregate(sum=Sum("total_price"))["sum"] or Decimal(0)
    booking.total_price = new_total
    booking.save(update_fields=["total_price"])

    # Jeśli payment istnieje i nie jest finalny → ustaw CANCELED (logicznie spójne z anulowaniem)
    p = getattr(booking, "payment", None)
    if p and p.status in (Payment.Status.CREATED, Payment.Status.PENDING, Payment.Status.AUTHORIZED):
        p.status = Payment.Status.CANCELED
        p.save(update_fields=["status", "updated_at"])

    messages.success(
        request,
        _("Rezerwacja „{event}” została anulowana i miejsce zwolnione.").format(event=item.event.name),
    )
    logger.info(f"Anulowano rezerwację: [booking_item_id={booking_item_id}, user={request.user.username}]")
    return redirect("booking:my_bookings")
