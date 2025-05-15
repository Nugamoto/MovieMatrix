import uuid
from unittest.mock import patch

from werkzeug.security import generate_password_hash


# ---------------------- HOME PAGE ---------------------- #

def test_home_page(client):
    """
    Should load the home page and contain the app title.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert b"MovieMatrix" in response.data


# ---------------------- LOGIN -------------------------- #

def test_login_get_form(client):
    """
    Should render the login form on GET /login.
    """
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data


def test_login_invalid_credentials(client):
    """
    Should reject invalid login credentials.
    """
    response = client.post("/login", data={
        "username": "nonexistent",
        "password": "wrong"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid username or password." in response.data


def test_login_valid(client, data_manager):
    """
    Should log the user in and redirect to user list.
    """
    username = f"login_{uuid.uuid4().hex[:6]}"
    email = f"{username}@example.com"
    password = "secure123"

    user = data_manager.add_user(username, email, "Login", password_hash=generate_password_hash("wrongpass"))
    data_manager.update_user(user.id, {"password_hash": generate_password_hash(password)})

    response = client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

    assert response.status_code == 200
    assert b"Welcome" in response.data


def test_logout(client, data_manager):
    """
    Should log out the user and redirect to login page.
    """
    username = "logoutuser"
    password = "bye123"
    data_manager.add_user(username, "logout@example.com", "Out", generate_password_hash(password))

    client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
    response = client.get("/logout", follow_redirects=True)

    assert response.status_code == 200
    assert b"You have been logged out." in response.data


def test_protected_route_requires_login(client):
    """
    Should redirect to login page when accessing protected route unauthenticated.
    """
    response = client.get("/users/1", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data or b"Please log in" in response.data


# ---------------------- ERROR HANDLING -------------------------- #

def test_forbidden_access_to_other_user_movies(client, data_manager):
    """
    Should redirect with a flash message when accessing another user's movies.
    """
    user1 = data_manager.add_user("user403a", "403a@example.com", "UserA", generate_password_hash("pass"))
    user2 = data_manager.add_user("user403b", "403b@example.com", "UserB", generate_password_hash("pass"))

    client.post("/login", data={"username": user1.username, "password": "pass"}, follow_redirects=True)

    response = client.get(f"/users/{user2.id}", follow_redirects=True)

    assert response.status_code == 200
    assert b"Access forbidden" in response.data  # Adjusted to match flash message


def test_nonexistent_route_returns_404(client):
    """
    Should render a custom 404 page when route is not found.
    """
    response = client.get("/some/random/page", follow_redirects=True)
    assert response.status_code == 404
    assert b"404" in response.data or b"not found" in response.data.lower()


def test_internal_server_error(client):
    """
    Should render 500 error page on unhandled exception.
    """
    with patch.object(client.application.data_manager, "get_all_users", side_effect=Exception("Boom")):
        response = client.get("/users", follow_redirects=True)

    assert response.status_code == 500
    assert b"500" in response.data or b"internal" in response.data.lower()
