from django.urls import path
from .views import event_list_view, event_detail_view

app_name = "events"

urlpatterns = [
    path('', event_list_view, name='events_list'),
    path('<int:pk>/', event_detail_view, name='event_detail'),
]