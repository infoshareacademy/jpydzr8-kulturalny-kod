from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from apps.events.models import Event
from apps.events.forms import EventForm

def role_required(role):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, "profile") or request.user.profile.role != role:
                return HttpResponseForbidden("Brak uprawnień do tej sekcji.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


@login_required
@role_required("super_user")
def super_user_events_list(request):
    events = Event.objects.all().order_by("-date")
    return render(request, "account/super_user_events_list.html", {"events": events})


@login_required
@role_required("super_user")
def super_user_event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("account:super_user_events_list")
    else:
        form = EventForm()
    return render(request, "account/super_user_event_form.html", {"form": form, "mode": "create"})


@login_required
@role_required("super_user")
def super_user_event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect("account:super_user_events_list")
    else:
        form = EventForm(instance=event)
    return render(request, "account/super_user_event_form.html", {"form": form, "mode": "edit", "event": event})


@login_required
@role_required("super_user")
def super_user_event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        event.delete()
        return redirect("account:super_user_events_list")
    return render(request, "account/super_user_event_delete_confirm.html", {"event": event})
