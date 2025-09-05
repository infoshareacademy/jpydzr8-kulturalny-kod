import pytest
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from apps.users.models import UserProfile


@pytest.fixture
def create_user(db):
    def make_user(username: str, email: str, password: str = "test123"):
        return User.objects.create_user(username=username, email=email, password=password)
    return make_user

@pytest.mark.django_db
def test_single_user_created(create_user):
    user = create_user("jan", "jan@example.com")

    assert user.username == "jan"
    assert user.email == "jan@example.com"
    
@pytest.mark.django_db
def test_multiple_users_created(create_user):
    user1 = create_user("jan", "jan@example.com")
    user2 = create_user("anna", "anna@example.com")

    assert User.objects.count() == 2

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
