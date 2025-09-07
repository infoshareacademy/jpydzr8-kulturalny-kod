from io import BytesIO
import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.users.models import UserProfile
from apps.users.forms import CustomUserCreationForm, CustomUserChangeForm, UserProfileForm


@pytest.mark.django_db
def test_user_create_form_clean_email():
    # create a user with an email
    User.objects.create_user(username="jan", email="jan@example.com", password="pass123")

    # try to create another user with the same email
    form_data = {"username": "jan2", "email": "jan@example.com", "password": "pass456"}
    form = CustomUserCreationForm(data=form_data)
    assert not form.is_valid()
    assert "email" in form.errors
    assert form.errors["email"] == ["Ten adres e-mail jest już zajęty."]

@pytest.mark.django_db
def test_user_create_form_validate_email():
    # create a user with an email

    # try to create another user with the same email
    form_data = {"username": "jan2", "email": "janexample.com", "password": "pass456"}
    form = CustomUserCreationForm(data=form_data)
    assert not form.is_valid()
    assert "email" in form.errors
    assert form.errors["email"] == ["Wprowadź poprawny adres email."]

@pytest.mark.django_db
def test_user_create_form_validate_password_match():
    # create a user with an email

    # try to create another user with the same email
    form_data = {"username": "jan2", "email": "jan@example.com", "password1": "pass456789", "password2": "pass45789"}
    form = CustomUserCreationForm(data=form_data)
    assert not form.is_valid()
    assert "password2" in form.errors
    assert form.errors["password2"] == ["Hasła w obu polach nie są zgodne."]

@pytest.mark.django_db
def test_user_create_form_validate_password_mix():
    # create a user with an email

    # try to create another user with the same email
    form_data = {"username": "jan2", "email": "jan@example.com", "password1": "pass", "password2": "pass"}
    form = CustomUserCreationForm(data=form_data)
    assert not form.is_valid()
    assert "password2" in form.errors
    assert form.errors["password2"] == ['To hasło jest za krótkie. Musi zawierać co najmniej 8 znaków.', 'To hasło jest zbyt powszechne.']

@pytest.mark.django_db
def test_user_create_form_validate_password_short():
    # create a user with an email

    # try to create another user with the same email
    form_data = {"username": "jan2", "email": "jan@example.com", "password1": "xhob53", "password2": "xhob53"}
    form = CustomUserCreationForm(data=form_data)
    assert not form.is_valid()
    assert "password2" in form.errors
    assert form.errors["password2"] == ['To hasło jest za krótkie. Musi zawierać co najmniej 8 znaków.']

@pytest.mark.django_db
def test_user_create_form_clean_names():
    # create a user with an email

    # try to create another user with the same email
    form_data = {
        "username": "jan", 
        "email": "jan@example.com",
        "first_name": "jan",
        "last_name": "kowalski",
        "password1": "xzg76dxvc5", 
        "password2": "xzg76dxvc5"
    }
    form = CustomUserCreationForm(data=form_data)
    assert form.is_valid()
    
    # cleaned_data contains the capitalized first name
    assert form.cleaned_data['first_name'] == "Jan"
    assert form.cleaned_data['last_name'] == "Kowalski"

@pytest.mark.django_db
def test_user_profile_form_valid():
    user = User.objects.create(username="jan", email="jan@example.com")
    # Create an empty UserProfile for this user first
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    size = (800, 600)
    storage = BytesIO()
    img = Image.new("RGB", size)
    img.save(storage, "JPEG")
    storage.seek(0)
    
    # Simulate uploading an image
    image = SimpleUploadedFile(
        name="test_image.jpg", content=storage.getvalue(), content_type="image/jpeg"
    )

    form_data = {}
    form_files = {'photo': image}

    form = UserProfileForm(data=form_data, files=form_files, instance=profile)
    
    assert form.is_valid()  # Form should be valid with file
    profile = form.save()
    assert profile.user == user
    assert profile.photo.name.startswith("profile_photos/jan_")

@pytest.mark.django_db
def test_user_profile_form_invalid_file():
    user = User.objects.create(username="jan2", email="jan2@example.com")
    
    # Invalid file type
    invalid_file = SimpleUploadedFile(
        name="test.txt",
        content=b"hello",
        content_type="text/plain"
    )

    form = UserProfileForm(data={}, files={'photo': invalid_file}, instance=UserProfile(user=user))
    
    assert not form.is_valid()  # depends on your validators
    assert 'photo' in form.errors
    assert form.errors["photo"] == ['Prześlij poprawny plik graficzny. Aktualnie przesłany plik nie jest grafiką\xa0lub jest uszkodzony.']
