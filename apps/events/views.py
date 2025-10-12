from django.shortcuts import render, get_object_or_404, redirect
from .models import Event
from kulturalny_kod.logger import get_logger
logger = get_logger(__name__)

def event_list_view(request):
    events = Event.objects.all()
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    show_all = request.GET.get('all')
    city = request.GET.get('city')

    if not show_all and not (from_date and to_date) and not city:
        return render(request, "events/events_list.html", {"events": []})

    if from_date and to_date:
        events = events.filter(date__range=[from_date, to_date])

    if city:
        events = events.filter(city=city.capitalize())
    logger.info(f"Wywołana lista eventów: {events} przez: {getattr(request.user, "username", "Anonymous")}")
    return render(request, "events/events_list.html", {
        "events": events
    })

def event_detail_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    logger.info(f"Wywołane szczegółu eventu: {event} przez: {getattr(request.user, "username", "Anonymous")}")
    return render(request, "events/event_detail.html", {"event": event})