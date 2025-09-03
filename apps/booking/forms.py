from django import forms

class BookingForm(forms.Form):
    full_name = forms.CharField(label='Imię i nazwisko', max_length=120)
    email = forms.EmailField(label='E-mail')
    quantity = forms.IntegerField(label='Liczba biletów', min_value=1, max_value=10)
