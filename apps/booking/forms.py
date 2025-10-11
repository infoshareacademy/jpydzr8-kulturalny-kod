from django import forms

class BookingForm(forms.Form):
    quantity = forms.IntegerField(label='Liczba biletów', min_value=1, max_value=10)
