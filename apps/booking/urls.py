from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # path('<int:event_id>/new/', views.booking_create, name='create'),
    path('<int:event_id>/new/', views.booking_view, name='create'),
    # path('success/<str:ticket_number>/', views.booking_success, name='success'),
    path('success/<str:booking_number>/', views.booking_success_multiple, name='success_multiple'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('checkout/', views.cart_checkout, name='cart_checkout')
]
