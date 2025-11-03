import json
import os
import pytest
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from apps.account.management.commands.load_users import Command

TEST_FILE_NAME = "test.json"


@pytest.fixture()
def loaded_users(django_user_model, django_db_blocker):
    command = Command()
    with django_db_blocker.unblock():
        command._load_users(file_name=TEST_FILE_NAME)
    return django_user_model.objects.all()


@pytest.fixture()
def users_from_json():
    """Load users from the test JSON file."""
    file_path = os.path.join(
        settings.BASE_DIR, "apps", "users", "media", "json_files", TEST_FILE_NAME
    )
    with open(file_path, "r", encoding="utf-8") as f:
        users_json = json.load(f)
    return users_json["users"]


@pytest.mark.django_db
def test_load_users_command(loaded_users):

    assert len(loaded_users) == 1


@pytest.mark.django_db
def test_login_after_loading_users(loaded_users, users_from_json):
    user_json = users_from_json[0]
    result_logged_in = authenticate(
        username=user_json["username"], password=user_json["password"]
    )
    result_denied = authenticate(
        username=user_json["username"], password="wrongpassword"
    )

    assert result_logged_in is not None
    assert result_denied is None


@pytest.mark.django_db
def test_correct_fields_after_loading_users(loaded_users, users_from_json):
    user_json = users_from_json[0]
    user_from_db = User.objects.get(username=user_json["username"])

    for key, value in user_json.items():
        if key != "password":  # Skip password check
            assert getattr(user_from_db, key) == value
