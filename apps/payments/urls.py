from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("webhook/<str:provider>/", views.webhook, name="webhook"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/remove/<int:event_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("confirm/", views.confirm_reservation, name="confirm"),
    path("start/", views.start_from_cart, name="start_from_cart"),
    path("success/", views.success, name="success"),
    path("fail/", views.fail, name="fail"),
]
