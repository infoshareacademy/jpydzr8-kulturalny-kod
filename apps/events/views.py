from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Event, EventSeat
from django.http import JsonResponse
from kulturalny_kod.logger import get_logger

logger = get_logger(__name__)


def event_list_view(request):
    events = Event.objects.all()
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    show_all = request.GET.get("all")
    city = request.GET.get("city")
    q = request.GET.get("q", "")

    if not show_all and not (from_date or to_date) and not city and not q:
        return render(request, "events/events_list.html", {"events": []})

    if from_date and to_date:
        events = events.filter(date__range=[from_date, to_date])
    elif from_date:
        events = events.filter(date__gte=from_date)
    elif to_date:
        events = events.filter(date__lte=to_date)

    if city:
        events = events.filter(city__iexact=city.strip())

    if q:
        q = q.strip()
        events = events.filter(
            Q(name__icontains=q)
            | Q(city__icontains=q)
            | Q(venue_area__venue__name__icontains=q)
            | Q(venue_area__name__icontains=q)
            | Q(description__icontains=q)
            | Q(highlights__icontains=q)
        )

    logger.info(
        f"Wywołana lista eventów: {events} przez: {getattr(request.user, 'username', 'Anonymous')}"
    )
    return render(request, "events/events_list.html", {"events": events})


def event_detail_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    logger.info(
        f"Wywołane szczegółu eventu: {event} przez: {getattr(request.user, 'username', 'Anonymous')}"
    )
    return render(request, "events/event_detail.html", {"event": event})


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
