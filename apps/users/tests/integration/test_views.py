import pytest
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.test import Client
from typing import cast


@pytest.fixture
def test_user(db):
    """
    Create a test user in the database.
    """
    user = User.objects.create_user(
        username="testuser",
        password="password123",
        email="testuser@example.com"
    )
    return user


def test_unauthorized_user_redirected_to_login():
    """
    Test that an unauthorized user is redirected to the login page when trying to access a protected page.

    This function creates a test client, sends a GET request to a protected URL,
    and checks if the response status code is 200 (OK) and if the response contains
    the login template.

    The function uses the `override_settings` decorator to temporarily set the
    `LOGIN_URL` to '/users/user_login.html' for the duration of the test.
    """
    client = Client()
    response = client.get("/users/home/", follow=True)  # follow redirect
    assert response.status_code == 200
    assert "users/user_login.html" in [t.name for t in response.templates]

@pytest.mark.django_db
def test_authorized_user_can_access_home(test_user):
    """
    Test that an authorized user can access the home page.

    This function creates a test client, logs in a user with the username 'testuser',
    sends a GET request to the home page URL, and checks if the response status code
    is 200 (OK) and if the response contains the home template.
    """
    client = Client()
    client.login(username=test_user.username, password="password123")
    response = client.get("/users/home/")
    assert response.status_code == 200
    assert "users/user_home.html" in [t.name for t in response.templates]

def test_authorized_user_is_redirected_to_home_uses_correct_template(test_user):
    client = Client()
    client.login(username=test_user.username, password="password123")
    response = client.get("/users/login/", follow=True)
    assert response.status_code == 200
    assert "users/user_home.html" in [t.name for t in response.templates]

def test_authorized_user_can_access_logout(test_user):
    client = Client()
    client.login(username=test_user.username, password="password123")

    # POST logout without follow to check the redirect itself
    response = client.post("/users/logout/")
    response = cast(HttpResponseRedirect, response)

    # Logout view should redirect to '/'
    assert response.status_code == 302
    assert response.url == "/"

def test_authorized_user_can_access_logout_uses_correct_template(test_user):
    client = Client()
    client.login(username=test_user.username, password="password123")

    final_response = client.post("/users/logout/", follow=True)
    assert final_response.status_code == 200
    assert "home.html" in [t.name for t in final_response.templates]

def test_authorized_user_is_redirected_to_home(test_user):
    client = Client()
    client.login(username=test_user.username, password="password123")
    response = client.get("/users/login/")
    response = cast(HttpResponseRedirect, response)
    
    assert response.status_code == 302
    assert response.url == "/users/home/"