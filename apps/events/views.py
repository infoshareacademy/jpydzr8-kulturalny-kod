from django.shortcuts import render
from .models import Event

def event_list_view(request):
    events = Event.objects.all()
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    show_all = request.GET.get('all')

    if not show_all and not (from_date and to_date):
        return render(request, "events/events_list.html", {"events": []})

    if from_date and to_date:
        events = events.filter(date__range=[from_date, to_date])

    return render(request, "events/events_list.html", {
        "events": events
    })
