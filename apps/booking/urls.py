from django.urls import path
from . import views

app_name = "booking"

urlpatterns = [
    path("event/<int:event_id>/", views.booking_view, name="booking_view"),
    path("success/<str:ticket_number>/", views.booking_success, name="success"),
    path("success-multiple/<int:booking_number>/", views.booking_success_multiple, name="success_multiple"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
    path("cancel-item/<int:booking_item_id>/", views.booking_item_cancel, name="cancel_item"),
]
