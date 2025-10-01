from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import UserProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
        return user

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ten adres e-mail jest już zajęty.")
        return email
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '')
        return first_name.capitalize()

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '')
        return last_name.capitalize()

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name")  # removed "password" field entirely

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the password field entirely, if it exists
        if 'password' in self.fields:
            self.fields.pop('password')
            
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '')
        return first_name.capitalize()

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '')
        return last_name.capitalize()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['photo']
