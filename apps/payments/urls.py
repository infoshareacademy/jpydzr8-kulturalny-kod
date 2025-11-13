from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("cart/", views.cart_view, name="cart"),
    path("cart/remove-item/<int:booking_item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/", views.checkout_and_pay, name="checkout"),
    path("<int:pk>/start/", views.start_payment, name="start"),
    path("<int:pk>/result/", views.result, name="result"),
    path("<int:pk>/simulate-success/", views.simulate_success, name="simulate_success"),
    path("<int:pk>/simulate-fail/", views.simulate_fail, name="simulate_fail"),
    path("webhook/<str:provider>/", views.webhook, name="webhook"),
]
