from django import forms

class BookingForm(forms.Form):
    # Usuń pola full_name i email - będą pobierane z zalogowanego użytkownika
    quantity = forms.IntegerField(label='Liczba biletów', min_value=1, max_value=10)
