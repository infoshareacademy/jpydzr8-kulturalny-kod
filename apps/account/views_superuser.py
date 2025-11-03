from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from apps.booking.models import BookingItem


def is_super_user(user):
    return hasattr(user, "profile") and user.profile.role == "super_user"


@login_required
@user_passes_test(is_super_user)
def super_user_dashboard(request):
    users = User.objects.all().select_related("profile")

    booking_items = BookingItem.objects.select_related(
        "booking__user",
        "event",
        "seat__seat__section",
    ).order_by("-booking__created_at")

    return render(
        request,
        "account/super_user_dashboard.html",
        {
            "users": users,
            "booking_items": booking_items,
        },
    )


@login_required
@user_passes_test(is_super_user)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user != request.user:
        user.delete()
    return redirect("account:super_user_dashboard")
