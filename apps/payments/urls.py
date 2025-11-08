from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("webhook/<str:provider>/", views.webhook, name="webhook"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("confirm/", views.confirm_reservation, name="confirm"),
    path("start/", views.start_from_cart, name="start_from_cart"),
    path("start/<int:booking_id>/", views.start_for_booking, name="start_for_booking"),
    path("payment/<int:pk>/start/", views.start_payment, name="start_payment"),
    path("success/", views.success, name="success"),
    path("fail/", views.fail, name="fail"),
]
