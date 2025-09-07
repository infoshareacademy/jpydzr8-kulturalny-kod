import pytest
from django.contrib.auth.models import User

from apps.users.forms import CustomUserChangeForm


def test_valid_form():
    user = User(username="anna")
    form = CustomUserChangeForm(instance=user, data={"username": "anna_now"})
    assert form.is_valid()

def test_user_change_valid_form_names():
    user = User(username="anna")
    form = CustomUserChangeForm(instance=user, data={"first_name": "anna", "last_name": "kowalska"})
    
    assert form.is_valid()
    assert form.cleaned_data["first_name"] == "Anna"  # capitalized
    assert form.cleaned_data["last_name"] == "Kowalska"  # capitalized

def test_user_change_valid_form_names_empty():
    user = User(username="XXXX")
    form = CustomUserChangeForm(instance=user, data={"first_name": "", "last_name": ""})

    assert form.is_valid()
    assert form.cleaned_data["first_name"] == ""
    assert form.cleaned_data["last_name"] == ""
