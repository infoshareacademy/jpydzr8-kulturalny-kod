from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Event, EventSeat
from django.http import JsonResponse
from kulturalny_kod.logger import get_logger
from apps.venues.models import Seat, SectionType
from apps.booking.utils_expire import expire_stale_locks

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
    expire_stale_locks(event=event)
    logger.info(
        f"Wywołane szczegółu eventu: {event} przez: {getattr(request.user, 'username', 'Anonymous')}"
    )
    return render(request, "events/event_detail.html", {"event": event})


# ✅ ADDED: mały helper do LENIWEGO utworzenia EventSeat z planu eventu
def _ensure_event_seats(event: Event) -> int:  # ADDED
    """
    Tworzy brakujące EventSeat dla wszystkich miejsc siedzących
    w planie podpiętym do eventu (event.seating_plan albo pierwszy z venue_area).
    Zwraca liczbę UTWORZONYCH rekordów.
    """  # ADDED
    plan = event.seating_plan or (event.venue_area.plans.order_by("id").first() if event.venue_area else None)  # ADDED
    if not plan:
        return 0  # ADDED
    created = 0  # ADDED
    # tylko siedzące (numerowane)
    for s in Seat.objects.filter(section__plan=plan, section__type=SectionType.SEATED).only("id"):  # ADDED
        _, was_created = EventSeat.objects.get_or_create(event=event, seat=s)  # ADDED
        if was_created:
            created += 1  # ADDED
    return created  # ADDED


def event_seats_json(request, event_id):
    event = get_object_or_404(Event, pk=event_id)  # CHANGED (by mieć event pod ręką i lazy-init)
    # ✅ CHANGED: jeśli brak EventSeat → utwórz je z planu
    if not EventSeat.objects.filter(event=event).exists():  # ADDED
        _ensure_event_seats(event)  # ADDED

    # ✅ CHANGED: zwracaj tylko WOLNE i TYLKO SIEDZĄCE (select potrzebuje numerowanych)
    seats = (
        EventSeat.objects.select_related("seat__section")
        .filter(event=event, is_reserved=False, seat__isnull=False, seat__section__type=SectionType.SEATED)  # CHANGED
        .values(
            "id",
            "seat__section__name",
            "seat__row",
            "seat__number",
            "is_reserved",
        )
        .order_by("seat__section__name", "seat__row", "seat__number")  # ADDED: stabilna kolejność
    )
    return JsonResponse({"seats": list(seats)})


def seats_for_event(request, pk):
    event = get_object_or_404(Event, pk=pk)  # CHANGED
    # ✅ CHANGED: lazy-init jak wyżej
    if not EventSeat.objects.filter(event=event).exists():  # ADDED
        _ensure_event_seats(event)  # ADDED

    # ✅ CHANGED: tylko wolne, numerowane
    seats = (
        EventSeat.objects.filter(event=event, is_reserved=False, seat__isnull=False, seat__section__type=SectionType.SEATED)  # CHANGED
        .select_related("seat__section")
        .values(
            "id",
            "seat__section__name",
            "seat__row",
            "seat__number",
            "is_reserved",
        )
        .order_by("seat__section__name", "seat__row", "seat__number")  # ADDED
    )
    return JsonResponse({"seats": list(seats)})
