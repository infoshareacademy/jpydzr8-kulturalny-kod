from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Payment
from .services.dummy import DummyProvider
from apps.booking.models import Booking, BookingItem
from apps.events.models import EventSeat
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from django.contrib import messages
from apps.booking.utils import send_booking_confirmation_email
from apps.booking.utils import make_qr_code, default_storage
from apps.booking.services import render_ticket_pdf_to_content
import os
from kulturalny_kod.logger import get_logger

logger = get_logger(__name__)

def _get_provider(name: str):
    return DummyProvider()

def _clear_booking_session(request: HttpRequest, payment: Payment) -> None:
    if request.session.get("booking_id") == payment.booking_id:
        request.session.pop("booking_id", None)
        request.session.modified = True

@login_required
def cart_view(request: HttpRequest) -> HttpResponse:
    booking_id = request.session.get("booking_id")
    booking = None
    items = []
    total_price = Decimal(0)

    if booking_id:
        booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
        items = list(booking.items.select_related("event", "seat__seat__section"))
        total_price = booking.total_price

    return render(
        request,
        "payments/cart.html",
        {"booking": booking, "items": items, "total_price": total_price},
    )


@require_http_methods(["POST"])
@login_required
def remove_from_cart(request: HttpRequest, booking_item_id: int) -> HttpResponse:
    item = get_object_or_404(BookingItem, pk=booking_item_id, booking__user=request.user)
    booking = item.booking

    # zwalniamy miejsce
    if item.seat_id:
        evseat = get_object_or_404(EventSeat, pk=item.seat_id)
        evseat.is_reserved = False
        evseat.save(update_fields=["is_reserved"])

    item.delete()

    total = sum(i.total_price for i in booking.items.all())
    booking.total_price = total
    booking.save(update_fields=["total_price"])

    if booking.items.count() == 0:
        request.session.pop("booking_id", None)
        request.session.modified = True

    return redirect("payments:cart")

@require_http_methods(["POST"])
@login_required
def checkout_and_pay(request: HttpRequest) -> HttpResponse:
    booking_id = request.session.get("booking_id")
    if not booking_id:
        return HttpResponseBadRequest("Koszyk jest pusty.")

    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    if booking.items.count() == 0:
        return HttpResponseBadRequest("Koszyk jest pusty.")

    payment = getattr(booking, "payment", None)

    if payment is None:
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            currency="PLN",
            description=f"Zakup biletów #{booking.pk}",
            provider=Payment.Provider.DUMMY,
            payer_email=request.user.email or "",
            status=Payment.Status.CREATED,
            metadata={"created_from": "cart"},
        )
        return redirect("payments:start", pk=payment.pk)

    if payment.is_final:
        if payment.status in (Payment.Status.FAILED, Payment.Status.CANCELED):
            # ➕ tylko w 15 minut od ostatniej aktualizacji
            if (timezone.now() - payment.updated_at) <= timedelta(minutes=15):
                payment.amount = booking.total_price
                payment.currency = "PLN"
                payment.description = f"Zakup biletów #{booking.pk}"
                payment.provider = Payment.Provider.DUMMY
                payment.payer_email = request.user.email or ""
                payment.status = Payment.Status.CREATED
                payment.external_id = ""
                payment.metadata = {"retry": True, "created_from": "cart"}
                payment.save(update_fields=[
                    "amount", "currency", "description", "provider",
                    "payer_email", "status", "external_id", "metadata", "updated_at"
                ])
                return redirect("payments:start", pk=payment.pk)
            # poza oknem 15 min
            messages.error(request, "Czas na ponowienie płatności minął. Dodaj ponownie miejsca do koszyka.")
            return redirect("payments:cart")

        # SUCCEEDED – pokaż wynik
        return redirect("payments:result", pk=payment.pk)

    # PENDING/AUTHORIZED – wróć do startu
    return redirect("payments:start", pk=payment.pk)


def start_payment(request: HttpRequest, pk: int):
    payment = get_object_or_404(Payment, pk=pk)
    if payment.is_final:
        return redirect("payments:result", pk=payment.pk)

    provider_name = getattr(settings, "PAYMENTS_DEFAULT_PROVIDER", "dummy")
    provider = _get_provider(provider_name)
    res = provider.create_session(
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description or "",
        metadata={
            "booking_id": payment.booking_id,
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
            {"payment": payment, "error": "Błąd tworzenia sesji płatności"},
        )

    payment.status = Payment.Status.PENDING
    payment.external_id = getattr(res, "external_id", "") or ""
    payment.provider = provider.name
    payment.save(update_fields=["status", "external_id", "provider", "updated_at"])

    redirect_url = getattr(res, "redirect_url", None)
    if redirect_url:
        return redirect(redirect_url)

    return render(request, "payments/start.html", {"payment": payment})

def result(request: HttpRequest, pk: int):
    payment = get_object_or_404(Payment, pk=pk)

    if payment.status == Payment.Status.SUCCEEDED:
        _clear_booking_session(request, payment)

        booking = payment.booking

        for item in booking.items.all():

            if item.pdf_file:  # jeśli ma już pdf, NIE generujemy ponownie
                continue

            # QR → zapis jak wcześniej
            qr_content = make_qr_code(item.ticket_number)
            qr_path = f"qr_codes/{item.ticket_number}.png"
            qr_saved_path = default_storage.save(qr_path, qr_content)
            qr_url = os.path.join(settings.MEDIA_URL, qr_saved_path)

            # BASE_URL dla PDF
            base_url = request.build_absolute_uri('/')

            # GENEROWANIE PDF
            pdf_content = render_ticket_pdf_to_content(
                event=item.event,
                booking_item=item,
                qr_url=qr_url,
                base_url=base_url,
            )

            # ZAPIS PDF DO STORAGE
            pdf_path = f"tickets/{item.ticket_number}.pdf"
            pdf_saved_path = default_storage.save(pdf_path, pdf_content)

            # ZAPIS ŚCIEŻKI PDF DO DB
            item.pdf_file.name = pdf_saved_path
            item.save(update_fields=["pdf_file"])

        # wysyłka maila tylko raz
        if not payment.metadata.get("confirmation_email_sent"):
            send_booking_confirmation_email(payment.booking)
            payment.metadata["confirmation_email_sent"] = True
            payment.save(update_fields=["metadata", "updated_at"])

    can_retry = (
        payment.status in (Payment.Status.FAILED, Payment.Status.CANCELED)
        and (timezone.now() - payment.updated_at) <= timedelta(minutes=15)
    )

    booking = payment.booking
    items = []
    if booking:
        items = list(
            booking.items.select_related(
                "event",
                "seat__seat__section",
                "event__venue",
                "event__venue_area__venue",
            )
        )

    return render(
        request,
        "payments/result.html",
        {
            "payment": payment,
            "can_retry": can_retry,
            "booking": booking,
            "items": items,
        },
    )



def simulate_success(request: HttpRequest, pk: int):
    payment = get_object_or_404(Payment, pk=pk)
    if not payment.is_final:
        payment.status = Payment.Status.SUCCEEDED
        payment.save(update_fields=["status", "updated_at"])
        _clear_booking_session(request, payment)
    return redirect("payments:result", pk=payment.pk)

def simulate_fail(request: HttpRequest, pk: int):
    payment = get_object_or_404(Payment, pk=pk)
    if not payment.is_final:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status", "updated_at"])
    return redirect("payments:result", pk=payment.pk)

@csrf_exempt
def webhook(request: HttpRequest, provider: str) -> HttpResponse:
    prov = _get_provider(provider)
    result = prov.verify_webhook(request)

    if not result.get("ok"):
        return HttpResponse("bad webhook", status=400)

    external_id = result.get("external_id")
    if not external_id:
        return HttpResponse("missing external_id", status=400)

    payment = Payment.objects.filter(external_id=external_id).first()
    if not payment:
        return HttpResponse("payment not found", status=404)

    status = (result.get("status") or "").lower()
    if status == "succeeded":
        payment.status = Payment.Status.SUCCEEDED
    elif status == "failed":
        payment.status = Payment.Status.FAILED
    elif status == "canceled":
        payment.status = Payment.Status.CANCELED

    payment.save(update_fields=["status", "updated_at"])
    return HttpResponse("ok")
