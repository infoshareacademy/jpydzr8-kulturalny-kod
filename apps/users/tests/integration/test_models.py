import pytest
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from apps.users.models import UserProfile


@pytest.mark.django_db
def test_create_user(django_user_model):
    # Create a user
    user = django_user_model.objects.create_user(
        username="jan",
        email="jan@example.com",
        password="test123"
    )

    assert user.username == "jan"
    assert user.email == "jan@example.com"
    assert django_user_model.objects.count() == 1
    
@pytest.mark.django_db
def test_multiple_users(django_user_model):
    user1 = django_user_model.objects.create_user("jan", "jan@example.com", "test123")
    user2 = django_user_model.objects.create_user("anna", "anna@example.com", "test123")

    assert django_user_model.objects.count() == 2

@pytest.mark.django_db
def test_user_profile_created():
    user = User.objects.create(username="jan", email="jan@example.com")
    profile = UserProfile.objects.get(user=user)

    assert profile.user.username == "jan"
    assert str(profile) == f"{user.username} Profile"

@pytest.mark.django_db
def test_login_password():
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="jan", password="correctpass")

    result = authenticate(username="jan", password="correctpass")

    assert result is not None

@pytest.mark.django_db
def test_login_wrong_password():
    from django.contrib.auth.models import User
    user = User.objects.create_user(username="jan", password="correctpass")

    result = authenticate(username="jan", password="wrongpass")

    assert result is None
