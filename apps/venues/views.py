from django.shortcuts import render, get_object_or_404
from .models import Venue

def venue_list(request):
    obiekty = Venue.objects.all().order_by("name")
    return render(request, "venues/lista.html", {"obiekty": obiekty})

def venue_detail(request, pk):
    obiekt = get_object_or_404(Venue, pk=pk)
    return render(request, "venues/szczegoly.html", {"obiekt": obiekt})