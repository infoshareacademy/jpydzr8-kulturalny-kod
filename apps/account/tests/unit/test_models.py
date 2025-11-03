import pytest
import datetime
from django.utils import timezone
from django.contrib.auth.models import User
from apps.account.models import user_profile_picture_path
from apps.account.models import UserProfile


def test_user_profile_picture_path_generates_correct_path(monkeypatch):
    user = User(username="XXX")
    user_profile = UserProfile(user=user)

    filename = "photo.png"

    # Patch timezone for predictable timestamp
    monkeypatch.setattr(
        timezone, "now", lambda: datetime.datetime(2025, 9, 5, 12, 0, 0)
    )

    path = user_profile_picture_path(user_profile, filename)
    assert path == "profile_photos/XXX_20250905120000.png"


def test_userprofile_str_unit():
    user = User(username="XXX")
    user_profile = UserProfile(user=user)
    assert str(user_profile) == "XXX Profile"
