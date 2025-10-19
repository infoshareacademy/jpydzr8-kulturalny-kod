from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from apps.booking.models import Booking


def is_super_user(user):
    return hasattr(user, "profile") and user.profile.role == "super_user"

@login_required
@user_passes_test(is_super_user)
def super_user_dashboard(request):
    users = User.objects.all().select_related('profile')
    bookings = Booking.objects.all().select_related('user', 'event')
    return render(request, 'users/super_user_dashboard.html', {
        "users": users,
        "bookings": bookings,
    })

@login_required
@user_passes_test(is_super_user)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user != request.user:
        user.delete()
    return redirect('users:super_user_dashboard')
