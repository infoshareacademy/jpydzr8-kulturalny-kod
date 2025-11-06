from django.contrib import messages
from django.utils.translation import gettext as _
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
from apps.booking.views import finalize_booking_after_payment
from kulturalny_kod.logger import get_logger

logger = get_logger(__name__)


def _get_provider(name: str):
    return DummyProvider()


def _build_cart_payload(request: HttpRequest) -> Dict[str, Any]:
    cart_session = request.session.get("cart", {})
    events_in_cart = []
    total_price = Decimal(0)
    event_back_url = None

    for event_id, seat_ids in cart_session.items():
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

            seat_price = (event.price or Decimal(0)) + (section.price_modifier or Decimal(0))
            seats_data.append({
                "id": evseat.id,
                "is_standing": evseat.seat is None,
                "section": section.name,
                "row": row,
                "number": number,
                "price": seat_price,
            })
            total_price += seat_price

        events_in_cart.append({"event": event, "seats": seats_data})

    if events_in_cart:
        unique_events = {item["event"].id for item in events_in_cart}
        if len(unique_events) == 1:
            only_event_id = next(iter(unique_events))
            event_back_url = reverse("events:event_detail", kwargs={"pk": only_event_id})

    return {
        "cart": events_in_cart,
        "total_price": total_price,
        "event_back_url": event_back_url,
    }


def start_payment(request: HttpRequest, pk: int):
    payment = get_object_or_404(Payment, pk=pk)
    logger.info(f"Start płatności dla Payment ID={pk}, user={request.user}")

    if payment.is_final:
        logger.warning(f"Payment ID={pk} już zakończony, przekierowanie do result")
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
        logger.error(f"Payment create_session FAIL – id={pk}, error={res.error}")
        return render(
            request,
            "payments/result.html",
            {"payment": payment, "error": res.error or _("Błąd płatności")},
        )

    payment.status = Payment.Status.PENDING
    payment.external_id = res.external_id or ""
    payment.provider = provider.name
    payment.save(update_fields=["status", "external_id", "provider", "updated_at"])
    logger.info(f"Payment session utworzona poprawnie, ID={pk}")

    return render(request, "payments/start.html", {"payment": payment})


# 🟡 Placeholder pod przyszłych providerów (PayU, P24, Stripe, itp.)
@csrf_exempt
def webhook(request: HttpRequest, provider: str) -> HttpResponse:
    """
    Placeholder webhook endpoint.
    Zostawiony na przyszłą integrację z providerami (PayU, P24, Stripe itp.).
    Na razie tylko loguje zapytanie i zwraca 200 OK.
    """
    logger.info(f"Webhook received from provider={provider} | method={request.method}")
    # Możesz tu później dodać logikę walidacji / update'u statusu płatności
    return HttpResponse(_("Webhook received (no provider logic implemented yet)."), status=200)


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

        events_in_cart.append({"event": event, "seats": seats_data})

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


@require_http_methods(["GET", "POST"])
@login_required
def confirm_reservation(request: HttpRequest) -> HttpResponse:
    """
    Krok po koszyku: podsumowanie pozycji i kwoty.
    POST → przejście do startu płatności z koszyka.
    """
    payload = _build_cart_payload(request)

    if not payload["cart"]:
        messages.info(request, _("Twój koszyk jest pusty."))
        return redirect("payments:cart")

    if request.method == "POST":
        return redirect("payments:start_from_cart")

    return render(
        request,
        "payments/confirm.html",
        {
            "cart": payload["cart"],
            "total_price": payload["total_price"],
            "event_back_url": payload["event_back_url"],
            "currency": "PLN",
        },
    )


@login_required
def start_from_cart(request: HttpRequest) -> HttpResponse:
    """
    Symulacja startu płatności bez zapisu do modeli.
    Zapisujemy jedynie 'last_payment' w sesji i wracamy na success.
    """
    payload = _build_cart_payload(request)
    if not payload["cart"]:
        messages.info(request, _("Twój koszyk jest pusty."))
        return redirect("payments:cart")

    total = payload["total_price"]
    request.session["last_payment"] = {"amount": str(total), "currency": "PLN"}
    request.session.modified = True
    logger.info(f"Start from cart – user={request.user}, kwota={total}")
    return redirect("payments:success")


@login_required
def success(request: HttpRequest) -> HttpResponse:
    """
    Płatność OK – po potwierdzeniu płatności tworzymy rezerwację, bilety PDF,
    wysyłamy e-mail i czyścimy koszyk.
    """
    try:
        booking = finalize_booking_after_payment(request)
        messages.success(
            request,
            _("Płatność zakończona pomyślnie. Rezerwacja została utworzona."),
        )
        logger.info(f"Płatność zakończona sukcesem – booking_id={booking.pk}, user={request.user}")
    except Exception as e:
        logger.error(f"finalize_booking_after_payment error: {e}")
        messages.error(request, _("Nie udało się utworzyć rezerwacji po płatności."))
        return redirect("payments:fail")

    request.session["cart"] = {}
    request.session.modified = True

    return redirect("booking:success_multiple", booking_number=booking.pk)


@login_required
def fail(request: HttpRequest) -> HttpResponse:
    """
    Płatność nieudana – koszyk zostaje, komunikat dla użytkownika.
    """
    messages.error(request, _("Płatność nie powiodła się. Spróbuj ponownie."))
    logger.warning(f"Płatność nieudana – user={request.user}")
    return redirect("payments:cart")
