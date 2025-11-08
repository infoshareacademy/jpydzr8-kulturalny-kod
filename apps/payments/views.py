from django.contrib import messages
from django.utils.translation import gettext as _
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Payment
from .services.dummy import DummyProvider
from apps.booking.models import Booking, BookingItem
from apps.booking.utils_expire import expire_stale_locks
from kulturalny_kod.logger import get_logger

logger = get_logger(__name__)


def _get_provider(name: str):
    return DummyProvider()


def start_payment(request: HttpRequest, pk: int):
    payment = get_object_or_404(
        Payment.objects.select_related("booking").prefetch_related("booking__items"),
        pk=pk
    )
    logger.info(f"Start płatności dla Payment ID={pk}, user={request.user}")

    if payment.is_final:
        logger.warning(f"Payment ID={pk} już zakończony, przekierowanie do result")
        return redirect("payments:success")

    provider_name = getattr(settings, "PAYMENTS_DEFAULT_PROVIDER", "dummy")
    provider = _get_provider(provider_name)

    booking = payment.booking  # może być None, ale w naszym flow już jest
    ticket_numbers = []
    if booking:
        try:
            ticket_numbers = list(booking.items.values_list("ticket_number", flat=True))
        except Exception:
            ticket_numbers = []

    email = payment.payer_email
    if not email and booking:
        email = booking.email or (getattr(booking, "user", None) and booking.user.email)

    continue_url = request.build_absolute_uri(reverse("payments:success"))
    notify_url = request.build_absolute_uri(reverse("payments:webhook", kwargs={"provider": provider.name}))
    customer_ip = request.META.get("REMOTE_ADDR", "127.0.0.1")

    res = provider.create_session(
        amount=Decimal(payment.amount),
        currency=payment.currency,
        description=payment.description or (f"Booking #{booking.id}" if booking else "Zakup biletów"),
        metadata={
            "payment_id": payment.pk,
            "booking_id": booking.id if booking else None,
            "ticket_numbers": ticket_numbers,
            "email": email,
            "continue_url": continue_url,
            "notify_url": notify_url,
            "customer_ip": customer_ip,
        },
    )

    if not res.ok:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status", "updated_at"])
        logger.error(f"Payment create_session FAIL – id={pk}, error={res.error}")
        return render(
            request,
            "payments/payment_result.html",
            {"payment": payment, "error": res.error or _("Błąd płatności")},
        )

    payment.status = Payment.Status.PENDING
    payment.external_id = res.external_id or ""
    payment.provider = provider.name
    payment.save(update_fields=["status", "external_id", "provider", "updated_at"])
    logger.info(f"Payment session utworzona poprawnie, ID={pk}")

    return render(request, "payments/payment_start.html", {"payment": payment})


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
    expire_stale_locks(user=request.user)
    booking_id = request.session.get("pay_booking_id")

    if not booking_id:
        messages.info(request, _("Twój koszyk jest pusty."))
        return render(
            request,
            "payments/cart.html",
            {"cart": [], "total_price": Decimal(0), "event_back_url": None},
        )

    booking = get_object_or_404(
        Booking.objects.prefetch_related("items__event", "items__seat__seat__section"),
        pk=booking_id, user=request.user
    )

    # 🔴 To jest kluczowe: klik „Przejdź do płatności” z koszyka:
    if request.method == "POST":
        return redirect("payments:confirm")  # -> widok order_review (renderuje payments/order_review.html)

    events_in_cart = []
    for item in booking.items.all():
        s = item.seat
        seats_data = [{
            "id": getattr(s, "id", None),
            "is_standing": not bool(getattr(s, "seat", None)),
            "section": (s.seat.section.name if getattr(s, "seat", None) else getattr(s, "section", None).name) if s else None,
            "row": s.seat.row if (s and s.seat) else None,
            "number": s.seat.number if (s and s.seat) else None,
            "price": item.total_price,
        }]
        events_in_cart.append({"event": item.event, "seats": seats_data})

    return render(
        request,
        "payments/cart.html",
        {
            "cart": events_in_cart,
            "total_price": booking.total_price,
            "event_back_url": None,
        },
    )



@require_http_methods(["POST"])
@login_required
def remove_from_cart(request: HttpRequest, item_id: int) -> HttpResponse:
    booking_id = request.session.get("pay_booking_id")
    if not booking_id:
        messages.info(request, _("Twój koszyk jest pusty."))
        return redirect("payments:cart")

    item = get_object_or_404(
        BookingItem.objects.select_related("booking"),
        pk=item_id,
        booking__id=booking_id,
        booking__user=request.user,
    )

    if item.seat:
        seat = item.seat
        seat.is_reserved = False
        seat.save(update_fields=["is_reserved"])

    # Usuń item i przelicz sumę
    booking = item.booking
    item.delete()
    from django.db.models import Sum
    new_total = booking.items.aggregate(sum=Sum("total_price"))["sum"] or Decimal(0)
    booking.total_price = new_total
    booking.save(update_fields=["total_price"])

    messages.success(request, _("Usunięto pozycję z koszyka."))
    return redirect("payments:cart")


@require_http_methods(["GET", "POST"])
@login_required
def confirm_reservation(request: HttpRequest) -> HttpResponse:
    expire_stale_locks(user=request.user)
    booking_id = request.session.get("pay_booking_id")

    if not booking_id:
        messages.info(request, _("Twój koszyk jest pusty."))
        return redirect("payments:cart")

    booking = get_object_or_404(
        Booking.objects.prefetch_related("items__event", "items__seat__seat__section"),
        pk=booking_id, user=request.user
    )

    if request.method == "POST":
        # Klik "Potwierdź" → start płatności dla TEGO booking
        return redirect("payments:start_for_booking", booking_id=booking.id)

    return render(
        request,
        "payments/order_review.html",
        {
            "booking": booking,
            "items": booking.items.all(),
            "total_price": booking.total_price,
            "currency": "PLN",
            "event_back_url": None,
        },
    )


@login_required
def start_from_cart(request: HttpRequest) -> HttpResponse:
    booking_id = request.session.get("pay_booking_id")
    if not booking_id:
        messages.info(request, _("Twój koszyk jest pusty."))
        return redirect("payments:cart")

    # przekieruj na „Zapłać teraz” dla bieżącego booking
    return redirect("payments:start_for_booking", booking_id=booking_id)


@login_required
def success(request: HttpRequest) -> HttpResponse:

    from apps.booking.models import Booking
    from apps.booking.services import render_ticket_pdf_to_content
    from apps.booking.utils import make_qr_code, send_booking_confirmation_email  # ✅
    from django.core.files.storage import default_storage
    import os

    booking_id = request.session.get("pay_booking_id")
    if not booking_id:
        messages.success(request, _("Płatność zakończona pomyślnie."))
        return redirect("booking:my_bookings")

    booking = get_object_or_404(
        Booking.objects.select_related("payment").prefetch_related("items__event"),
        pk=booking_id,
        user=request.user,
    )

    for item in booking.items.all():
        if item.pdf_file:
            continue

        qr_content = make_qr_code(item.ticket_number)
        qr_path = f"qr_codes/{item.ticket_number}.png"
        qr_saved_path = default_storage.save(qr_path, qr_content)
        qr_url = os.path.join(settings.MEDIA_URL, qr_saved_path)

        pdf_content = render_ticket_pdf_to_content(
            event=item.event,
            booking_item=item,
            qr_url=qr_url,
        )
        pdf_path = f"tickets/{item.ticket_number}.pdf"
        pdf_saved_path = default_storage.save(pdf_path, pdf_content)

        item.pdf_file.name = pdf_saved_path
        item.save(update_fields=["pdf_file"])

    send_booking_confirmation_email(booking)

    request.session.pop("pay_booking_id", None)
    request.session["cart"] = {}
    request.session.modified = True

    messages.success(
        request,
        _("Płatność zakończona pomyślnie. Rezerwacja została sfinalizowana."),
    )
    return redirect("booking:success_multiple", booking_number=booking.pk)



@login_required
def fail(request: HttpRequest) -> HttpResponse:
    messages.error(request, _("Płatność nie powiodła się. Spróbuj ponownie."))
    logger.warning(f"Płatność nieudana – user={request.user}")
    return redirect("booking:my_bookings")


@login_required
def start_for_booking(request: HttpRequest, booking_id: int) -> HttpResponse:
    """
    Start płatności dla KONKRETNEJ rezerwacji (booking_id).
    Tworzy Payment jeśli nie istnieje i przekierowuje do start_payment.
    """
    booking = get_object_or_404(
        Booking.objects.select_related("payment"),
        pk=booking_id, user=request.user
    )

    payment = getattr(booking, "payment", None)
    if payment is None:
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            currency="PLN",
            provider=Payment.Provider.DUMMY,
            status=Payment.Status.CREATED,
            payer_email=booking.email or request.user.email,
            description=f"Booking #{booking.id}",
        )

    # ustaw bieżący booking w sesji (confirm/success będą miały kontekst)
    request.session["pay_booking_id"] = booking.id
    request.session.modified = True

    return redirect("payments:start_payment", pk=payment.pk)