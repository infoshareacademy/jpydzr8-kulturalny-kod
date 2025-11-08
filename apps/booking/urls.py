from django.urls import path
from . import views

app_name = "booking"

urlpatterns = [
    path("<int:event_id>/new/", views.booking_view, name="booking_form"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
    path(
        "cancel_item/<int:booking_item_id>/",
        views.booking_item_cancel,
        name="cancel_item",
    ),
    path("ticket/<int:booking_item_id>/", views.ticket_pdf, name="ticket_pdf"),
]
