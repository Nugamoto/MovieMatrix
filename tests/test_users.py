import uuid

import pytest
from werkzeug.security import generate_password_hash


# ---------------------- Helpers -------------------------- #

def create_user_and_login(client, data_manager, username=None):
    """Create and log in a test user."""
    unique = uuid.uuid4().hex[:6]
    username = username or f"user_{unique}"
    email = f"{username}@example.com"
    user = data_manager.add_user(username, email, "Test", generate_password_hash("secret123"))
    client.post("/login", data={"username": username, "password": "secret123"}, follow_redirects=True)
    return user


def create_valid_user_form():
    """Generate a dictionary with valid user form data."""
    username = f"User_{uuid.uuid4().hex[:6]}"
    return {
        "username": username,
        "email": f"{username}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "age": "28",
        "password": "password123",
        "confirm_password": "password123"
    }


# ---------------------- USERS -------------------------- #

def test_list_users(client):
    response = client.get("/users", follow_redirects=True)
    assert response.status_code == 200
    assert b"Users" in response.data
    assert b"Add User" in response.data


def test_add_user_valid(client):
    form = create_valid_user_form()
    response = client.post("/users/add", data=form, follow_redirects=True)
    assert response.status_code == 200
    assert bytes(form["username"], "utf-8") in response.data
    assert b"created" in response.data


@pytest.mark.parametrize("field,value,error_message", [
    ("username", "", b"Invalid username"),
    ("email", "invalid@", b"Invalid e-mail"),
    ("first_name", "!!", b"First name"),
    ("password", "", b"Passwords do not match"),
    ("confirm_password", "wrong", b"Passwords do not match"),
])
def test_add_user_invalid_input(client, field, value, error_message):
    form = create_valid_user_form()
    form[field] = value

    response = client.post("/users/add", data=form, follow_redirects=True)
    assert response.status_code == 200
    assert error_message in response.data


def test_update_user_valid(client, data_manager):
    user = create_user_and_login(client, data_manager, "updateuser")
    response = client.post(f"/users/edit/{user.id}", data={
        "username": "updateuser",
        "email": "updated@example.com",
        "first_name": "Updated",
        "last_name": "Name",
        "age": "35"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"User updated." in response.data


@pytest.mark.parametrize("field,value,error_msg", [
    ("username", "", b"Invalid username"),
    ("email", "not-an-email", b"Invalid e-mail"),
    ("first_name", "123", b"First name"),
    ("last_name", "!@#", b"Last name"),
])
def test_update_user_invalid_input(client, data_manager, field, value, error_msg):
    unique = uuid.uuid4().hex[:6]
    username = f"user_{unique}"
    email = f"{username}@example.com"

    user = data_manager.add_user(
        username, email, "Valid", generate_password_hash("secret123"), "Valid", 30
    )
    client.post("/login", data={"username": username, "password": "secret123"}, follow_redirects=True)

    form = {
        "username": username,
        "email": email,
        "first_name": "Valid",
        "last_name": "Valid",
        "age": "30",
    }
    form[field] = value

    response = client.post(f"/users/edit/{user.id}", data=form, follow_redirects=True)
    assert response.status_code == 200
    assert error_msg in response.data


def test_update_user_unauthorized(client, data_manager):
    owner = create_user_and_login(client, data_manager, "owner")
    victim = data_manager.add_user("victim", "v@example.com", "Victim", generate_password_hash("pw"))

    response = client.post(
        f"/users/edit/{victim.id}",
        data={
            "username": "hacker",
            "email": "hack@evil.com",
            "first_name": "Evil",
            "last_name": "Hacker",
            "age": "99"
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Access forbidden" in response.data


def test_delete_user_valid(client, data_manager):
    user = create_user_and_login(client, data_manager, "deleteuser")
    response = client.post(f"/users/delete/{user.id}", follow_redirects=True)
    assert response.status_code == 200
    assert b"deleted" in response.data


def test_delete_user_invalid(client, data_manager):
    user1 = create_user_and_login(client, data_manager, "owner")
    user2 = data_manager.add_user("target", "target@example.com", "Target", generate_password_hash("x"))

    response = client.post(f"/users/delete/{user2.id}", follow_redirects=True)
    assert response.status_code == 200
    assert b"Access forbidden" in response.data


def test_change_password_valid(client, data_manager):
    user = create_user_and_login(client, data_manager, "changepw")
    response = client.post(f"/users/{user.id}/change_password", data={
        "current_password": "secret123",
        "new_password": "newpass123",
        "confirm_password": "newpass123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Password updated successfully" in response.data


@pytest.mark.parametrize("current_pw,new_pw,confirm_pw,error_msg", [
    ("wrongpass", "new", "new", b"Current password is incorrect"),
    ("secret123", "new", "different", b"do not match"),
    ("secret123", "secret123", "secret123", b"must differ from current password"),
])
def test_change_password_invalid(client, data_manager, current_pw, new_pw, confirm_pw, error_msg):
    user = create_user_and_login(client, data_manager)
    response = client.post(f"/users/{user.id}/change_password", data={
        "current_password": current_pw,
        "new_password": new_pw,
        "confirm_password": confirm_pw
    }, follow_redirects=True)
    assert response.status_code == 200
    assert error_msg in response.data


def test_change_password_unauthorized(client, data_manager):
    user1 = create_user_and_login(client, data_manager, "one")
    user2 = data_manager.add_user("two", "two@example.com", "Two", generate_password_hash("pw"))

    response = client.post(
        f"/users/{user2.id}/change_password",
        data={
            "current_password": "pw",
            "new_password": "newpw",
            "confirm_password": "newpw"
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Access forbidden" in response.data
