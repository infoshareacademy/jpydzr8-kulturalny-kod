from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "name",
            "date",
            "city",
            "venue",
            "total_seats",
            "available_seats",
            "price",
            "description",
            "highlights",
        ]
        widgets = {
            "date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "highlights": forms.Textarea(attrs={"rows": 2}),
        }
