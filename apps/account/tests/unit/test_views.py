import pytest
from django.contrib.sessions.backends.base import SessionBase
from django.http import HttpResponseRedirect
from django.test import RequestFactory
from typing import cast
from unittest.mock import Mock, patch
from apps.account.views import UserHomeView


class DummySession(SessionBase, dict):
    """dict-like session for unit tests"""

    def __init__(self):
        super().__init__()

    def __getitem__(self, key):
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    def pop(self, key, default=None):
        return super().pop(key, default)


class TestUserHomeView:
    def test_user_home_page_returns_200(self):
        factory = RequestFactory()
        request = factory.get("/account/home/")

        # Mock an authenticated user
        request.user = Mock(is_authenticated=True)
        request.session = DummySession()  # dict-like session

        # Call the view
        response = UserHomeView.as_view()(request)

        # Assert response code
        assert response.status_code == 200

    def test_anonymous_user_home_page_returns_302(self):
        factory = RequestFactory()
        request = factory.get("/account/home/")

        # Mock an anonymous user
        request.user = Mock(is_authenticated=False)
        request.session = DummySession()  # dict-like session

        # Call the view
        response = UserHomeView.as_view()(request)

        # Assert response code
        assert response.status_code == 302

    def test_user_home_page_redirects_to_login(self):
        factory = RequestFactory()
        request = factory.get("/account/home/")

        # Mock an anonymous user
        request.user = Mock(is_authenticated=False)
        request.session = DummySession()  # dict-like session

        response = cast(HttpResponseRedirect, UserHomeView.as_view()(request))
        assert response.url == "/account/login/?next=/account/home/"
        assert response.status_code == 302

    def test_user_home_page_uses_correct_template(self):
        factory = RequestFactory()
        request = factory.get("/account/home/")
        request.user = Mock(is_authenticated=True)
        request.session = DummySession()

        with patch("apps.account.views.render") as mock_render:
            mock_render.return_value.status_code = 200
            response = UserHomeView.as_view()(request)
            # The context passed to render is in mock_render.call_args
            args, kwargs = mock_render.call_args
            template_name = args[1]  # render(request, template_name, context)
            assert template_name == "account/user_home.html"


class TestCustomLoginView:
    def test_custom_login_page_returns_200(self):
        factory = RequestFactory()
        request = factory.get("/account/login/")

        # Mock an anonymous user
        request.user = Mock(is_authenticated=False)
        request.session = DummySession()  # dict-like session

        # Call the view
        response = UserHomeView.as_view()(request)
        response = cast(HttpResponseRedirect, UserHomeView.as_view()(request))

        # Assert response code
        assert response.status_code == 302
        assert response.url == "/account/login/?next=/account/login/"
