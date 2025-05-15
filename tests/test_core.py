"""
Pytest tests for Flask application routes, covering public pages, authentication,
and error handling scenarios for the MovieMatrix application.
"""
import uuid
from unittest.mock import patch

import pytest
from werkzeug.security import generate_password_hash


# ---------------------- CORE ROUTES ---------------------- #

@pytest.mark.usefixtures("client")
class TestPublicRoutes:
    """
    Test public-facing routes that do not require authentication.
    """

    def test_home_page(self, client):
        """
        Should return 200 and render the home page with application name.
        """
        response = client.get("/")
        assert response.status_code == 200
        assert b"MovieMatrix" in response.data

    def test_login_get_form(self, client):
        """
        Should return 200 and display the login form.
        """
        response = client.get("/login")
        assert response.status_code == 200
        assert b"Login" in response.data

    def test_nonexistent_route_returns_404(self, client):
        """
        Should return a 404 status and show 'not found' message for invalid URLs.
        """
        response = client.get("/some/random/page")
        assert response.status_code == 404
        assert b"404" in response.data
        assert b"not found" in response.data.lower()


@pytest.mark.usefixtures("client", "data_manager")
class TestAuthentication:
    """
    Test authentication flows: login, logout, and access control.
    """

    def test_login_invalid_credentials(self, client):
        """
        Should re-render login with error on invalid credentials.
        """
        response = client.post(
            "/login",
            data={"username": "nonexistent", "password": "wrong"},
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Invalid username or password." in response.data

    def test_login_valid(self, client, data_manager):
        """
        Should authenticate user and display welcome message on valid login.
        """
        username = f"login_{uuid.uuid4().hex[:6]}"
        email = f"{username}@example.com"
        password = "secure123"

        user = data_manager.add_user(username, email, "Login", password_hash=generate_password_hash("wrongpass"))
        data_manager.update_user(user.id, {"password_hash": generate_password_hash(password)})

        response = client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Welcome" in response.data

    def test_logout(self, client, register_user_and_login):
        """
        Should log out authenticated user and show logout confirmation.
        """
        register_user_and_login(prefix="logoutuser")
        response = client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"You have been logged out." in response.data

    def test_protected_route_requires_login(self, client):
        """
        Should redirect unauthenticated access to login prompt on protected routes.
        """
        response = client.get("/users/1", follow_redirects=True)
        assert response.status_code == 200
        assert b"Login" in response.data or b"Please log in" in response.data


@pytest.mark.usefixtures("client", "data_manager")
class TestErrorHandling:
    """
    Test application responses to error conditions and exceptions.
    """

    def test_forbidden_access_to_other_user_movies(self, client, data_manager):
        """
        Should prevent one user from viewing another user's movies and show forbidden message.
        """
        user1 = data_manager.add_user("user403a", "403a@example.com", "UserA", generate_password_hash("pass"))
        user2 = data_manager.add_user("user403b", "403b@example.com", "UserB", generate_password_hash("pass"))

        client.post(
            "/login",
            data={"username": user1.username, "password": "pass"},
            follow_redirects=True
        )
        response = client.get(f"/users/{user2.id}", follow_redirects=True)
        assert response.status_code == 200
        assert b"Access forbidden" in response.data

    def test_internal_server_error(self, client):
        """
        Should render custom 500 page when an exception is raised.
        """
        with patch.object(
                client.application.data_manager,
                "get_all_users",
                side_effect=Exception("Boom")
        ):
            response = client.get("/users", follow_redirects=True)
        assert response.status_code == 500
        assert b"500" in response.data
        assert b"server error" in response.data.lower()
