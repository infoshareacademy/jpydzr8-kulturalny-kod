from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.db.models.functions import TruncDate
from django.db.models import Sum

from .models import Event, EventSeat
from kulturalny_kod.logger import get_logger

logger = get_logger(__name__)


def _truthy(val: str | None) -> bool:
    return (val or "").lower() in {"1", "on", "true", "yes", "y"}


def event_list_view(request):
    """
    Lista wydarzeń:
    - domyślnie: tylko dziś i przyszłość, rosnąco po dacie
    - checkbox 'dostepne=1' → tylko wydarzenia z wolnymi miejscami (>0)
    - filtry: q (nazwa/miasto/opis), city, from_date, to_date (po samej dacie)
    """
    today = timezone.localdate()
    show_available_only = _truthy(request.GET.get("dostepne"))

    # Bazowy queryset + adnotacje: data bez czasu i dostępna pula miejsc z EventSeat
    qs = (
        Event.objects
        .annotate(date_only=TruncDate("date"))
        .annotate(
            available_now=Count(
                "event_seats",
                filter=Q(event_seats__is_reserved=False),
            )
        )
    )

    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(city__icontains=q)
            | Q(venue_area__venue__name__icontains=q)
            | Q(venue_area__name__icontains=q)
            | Q(description__icontains=q)
            | Q(highlights__icontains=q)
        )

    city = (request.GET.get("city") or "").strip()
    if city:
        qs = qs.filter(city__icontains=city)

    from_date = (request.GET.get("from_date") or "").strip()
    to_date = (request.GET.get("to_date") or "").strip()
    if from_date:
        qs = qs.filter(date_only__gte=from_date)
    if to_date:
        qs = qs.filter(date_only__lte=to_date)

    if show_available_only:
        qs = qs.filter(available_now__gt=0)

    qs = qs.filter(date_only__gte=today).order_by("date")

    events = list(qs)  # materializacja (stabilne atrybuty w szablonie)

    logger.info(
        f"Lista eventów: {len(events)} wyników; dostępne_only={show_available_only}; "
        f"user={getattr(request.user, 'username', 'Anonymous')}"
    )

    return render(
        request,
        "events/events_list.html",
        {
            "events": events,
            "show_available_only": show_available_only,  # do zbindowania checkboxa w szablonie
        },
    )


def event_detail_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    available_now = EventSeat.objects.filter(event=event, is_reserved=False).count()

    logger.info(
        f"Wywołane szczegóły eventu: {event} przez: {getattr(request.user, 'username', 'Anonymous')}"
    )
    return render(
        request,
        "events/event_detail.html",
        {"event": event, "available_now": available_now},
    )


def event_seats_json(request, event_id):
    seats = (
        EventSeat.objects.select_related("seat__section")
        .filter(event_id=event_id)
        .values(
            "id",
            "seat__section__name",
            "seat__row",
            "seat__number",
            "is_reserved",
        )
    )
    return JsonResponse({"seats": list(seats)})


def seats_for_event(request, pk):
    seats = (
        EventSeat.objects.filter(event_id=pk)
        .select_related("seat__section")
        .values(
            "id",
            "seat__section__name",
            "seat__row",
            "seat__number",
            "is_reserved",
        )
    )
    return JsonResponse({"seats": list(seats)})