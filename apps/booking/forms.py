from django import forms


class BookingForm(forms.Form):
    quantity = forms.IntegerField(initial=1, required=False, widget=forms.HiddenInput())
