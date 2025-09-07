from decimal import Decimal
from typing import Dict, Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import Payment
from .services.dummy import DummyProvider


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
            "ticket_number": payment.booking.ticket_number if payment.booking_id else None,
            "email": payment.payer_email or payment.booking.email if payment.booking_id else None,
            "continue_url": request.build_absolute_uri(reverse("payments:result", kwargs={"pk": payment.pk})),
            "notify_url": request.build_absolute_uri(reverse("payments:webhook", kwargs={"provider": provider.name})),
            "customer_ip": request.META.get("REMOTE_ADDR", "127.0.0.1"),
        },
    )

    if not res.ok:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status", "updated_at"])
        return render(request, "payments/result.html", {"payment": payment, "error": res.error or "Błąd płatności"})

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
