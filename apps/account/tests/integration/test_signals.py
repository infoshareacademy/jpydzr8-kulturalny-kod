import pytest
from django.contrib.auth import get_user_model
from apps.account.models import UserProfile

User = get_user_model()


@pytest.mark.django_db
def test_user_creation_creates_profile():
    # Create a user
    user = User.objects.create_user(username="jan", password="test123")

    # Signal should automatically create UserProfile
    profile = UserProfile.objects.get(user=user)

    assert profile.user == user
    assert hasattr(user, "profile")
