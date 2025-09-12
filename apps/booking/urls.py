from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('<int:event_id>/new/', views.booking_create, name='create'),
    path('success/<str:ticket_number>/', views.booking_success, name='success'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
]
