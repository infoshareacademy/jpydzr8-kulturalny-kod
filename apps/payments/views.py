from decimal import Decimal
from typing import Dict, Any

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Payment
from .services.dummy import DummyProvider
from apps.events.models import Event, EventSeat


def _get_provider(name: str):
    return DummyProvider()


def start_payment(request: HttpRequest, pk: int):
    payment = get_object_or_404(Payment, pk=pk)

    if payment.is_final:
        return redirect("payments:result", pk=payment.pk)

    provider_name = getattr(settings, "PAYMENTS_DEFAULT_PROVIDER", "dummy")
    provider = _get_provider(provider_name)

    res = provider.create_session(
        amount=Decimal(payment.amount),
        currency=payment.currency,
        description=payment.description or "",
        metadata={
            "booking_id": payment.booking_id,
            "ticket_number": (
                payment.booking.ticket_number if payment.booking_id else None
            ),
            "email": (
                payment.payer_email or payment.booking.email
                if payment.booking_id
                else None
            ),
            "continue_url": request.build_absolute_uri(
                reverse("payments:result", kwargs={"pk": payment.pk})
            ),
            "notify_url": request.build_absolute_uri(
                reverse("payments:webhook", kwargs={"provider": provider.name})
            ),
            "customer_ip": request.META.get("REMOTE_ADDR", "127.0.0.1"),
        },
    )

    if not res.ok:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status", "updated_at"])
        return render(
            request,
            "payments/result.html",
            {"payment": payment, "error": res.error or "Błąd płatności"},
        )

    payment.status = Payment.Status.PENDING
    payment.external_id = res.external_id or ""
    payment.provider = provider.name
    payment.save(update_fields=["status", "external_id", "provider", "updated_at"])

    return render(request, "payments/start.html", {"payment": payment})


def result(request: HttpRequest, pk: int):
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, "payments/result.html", {"payment": payment})


def simulate_success(request: HttpRequest, pk: int):
    payment = get_object_or_404(Payment, pk=pk)
    if not payment.is_final:
        payment.status = Payment.Status.SUCCEEDED
        payment.save(update_fields=["status", "updated_at"])
    return redirect("payments:result", pk=payment.pk)


def simulate_fail(request: HttpRequest, pk: int):
    payment = get_object_or_404(Payment, pk=pk)
    if not payment.is_final:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status", "updated_at"])
    return redirect("payments:result", pk=payment.pk)


@csrf_exempt
def webhook(request: HttpRequest, provider: str) -> HttpResponse:

    if provider != "dummy":
        return HttpResponse("unsupported provider", status=400)
    return HttpResponse("ok")


@require_http_methods(["GET", "POST"])
@login_required
def cart_view(request: HttpRequest) -> HttpResponse:
    user = request.user
    cart = request.session.get("cart", {})
    event_back_url = None
    events_in_cart = []
    total_price = Decimal(0)

    for event_id, seat_ids in cart.items():
        event = Event.objects.get(pk=int(event_id))
        seats_data = []

        for seat_id in seat_ids:
            evseat = EventSeat.objects.select_related("seat__section").get(pk=seat_id)

            if evseat.seat:
                section = evseat.seat.section
                row = evseat.seat.row
                number = evseat.seat.number
            else:
                section = evseat.section
                row = None
                number = None

            seat_price = event.price + section.price_modifier

            seats_data.append({
                "id": evseat.id,
                "is_standing": evseat.seat is None,
                "section": section.name,
                "row": row,
                "number": number,
                "price": seat_price,
            })

            total_price += seat_price

        events_in_cart.append({
            "event": event,
            "seats": seats_data,
        })

    if events_in_cart:
        unique_events = {item["event"].id for item in events_in_cart}
        if len(unique_events) == 1:
            only_event_id = next(iter(unique_events))
            event_back_url = reverse("events:event_detail", kwargs={"pk": only_event_id})

    return render(
        request,
        "payments/cart.html",
        {
            "cart": events_in_cart,
            "total_price": total_price,
            "event_back_url": event_back_url,
        },
    )


@require_http_methods(["POST"])
@login_required
def remove_from_cart(request: HttpRequest, event_id: int) -> HttpResponse:
    seat_id = request.POST.get("seat_id")
    cart = request.session.get("cart", {})

    if str(event_id) in cart and seat_id:
        try:
            seat_id = int(seat_id)
            cart[str(event_id)].remove(seat_id)
            if not cart[str(event_id)]:
                del cart[str(event_id)]
        except ValueError:
            pass

        request.session["cart"] = cart
        request.session.modified = True

    return redirect("payments:cart")
