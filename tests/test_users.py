"""
Pytest tests for user-related Flask routes including listing, adding, modifying,
password change, and deletion of users, covering valid flows, invalid inputs,
and access control.
"""
import uuid

import pytest
from werkzeug.security import generate_password_hash


# ---------------------- USER ROUTES ---------------------- #

@pytest.mark.usefixtures("client")
class TestUserListAndAdd:
    """
    Test listing users and adding new users via form submissions.
    """

    def valid_user_form(self):
        """
        Generate a valid user registration form payload with unique values.

        Returns:
            dict: Form data for a valid user.
        """
        unique = uuid.uuid4().hex[:6]
        username = f"User_{unique}"
        return {
            "username": username,
            "email": f"{username}@example.com",
            "first_name": "Test",
            "last_name": "User",
            "age": "28",
            "password": "password123",
            "confirm_password": "password123",
        }

    def test_list_users(self, client):
        """
        Should return 200 and display the users list page with Add User link.
        """
        response = client.get("/users", follow_redirects=True)
        assert response.status_code == 200
        assert b"Users" in response.data
        assert b"Add User" in response.data

    def test_add_user_valid(self, client):
        """
        Should create a new user when form input is valid.
        """
        form = self.valid_user_form()
        response = client.post("/users/add", data=form, follow_redirects=True)
        assert response.status_code == 200
        assert bytes(form["username"], "utf-8") in response.data
        assert b"created" in response.data

    @pytest.mark.parametrize(
        "field,value,error_message",
        [
            ("username", "", b"Invalid username"),
            ("email", "invalid@", b"Invalid e-mail"),
            ("first_name", "!!", b"First name"),
            ("password", "", b"Passwords do not match"),
            ("confirm_password", "wrong", b"Passwords do not match"),
        ],
    )
    def test_add_user_invalid_input(self, client, field, value, error_message):
        """
        Should display error messages when form input is invalid.

        Args:
            field (str): Form field to invalidate.
            value: Invalid value for the field.
            error_message (bytes): Expected error substring in response.
        """
        form = self.valid_user_form()
        form[field] = value
        response = client.post("/users/add", data=form, follow_redirects=True)
        assert response.status_code == 200
        assert error_message in response.data


@pytest.mark.usefixtures("client", "data_manager", "register_user_and_login")
class TestUserModification:
    """
    Test updating and deleting users, including unauthorized access handling.
    """

    def test_update_user_valid(self, register_user_and_login, client):
        """
        Should update user details when input is valid.
        """
        user = register_user_and_login(prefix="updateuser")
        response = client.post(
            f"/users/edit/{user['username']}".replace(
                user['username'],
                str(client.application.data_manager.get_user_by_username(user['username']).id)
            ),
            data={
                "username": user['username'],
                "email": "updated@example.com",
                "first_name": "Updated",
                "last_name": "Name",
                "age": "35",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"User updated." in response.data

    @pytest.mark.parametrize(
        "field,value,error_msg",
        [
            ("username", "", b"Invalid username"),
            ("email", "not-an-email", b"Invalid e-mail"),
            ("first_name", "123", b"First name"),
            ("last_name", "!@#", b"Last name"),
        ],
    )
    def test_update_user_invalid_input(self, register_user_and_login, client, data_manager, field, value, error_msg):
        """
        Should show error when updating user with invalid data.
        """
        user = register_user_and_login(prefix="validuser")
        user_obj = data_manager.get_user_by_username(user['username'])
        form = {
            "username": user['username'],
            "email": user['email'],
            "first_name": "Valid",
            "last_name": "Valid",
            "age": "30",
        }
        form[field] = value
        response = client.post(f"/users/edit/{user_obj.id}", data=form, follow_redirects=True)
        assert response.status_code == 200
        assert error_msg in response.data

    def test_update_user_unauthorized(self, register_user_and_login, client, data_manager):
        """
        Should forbid editing another user's profile.
        """
        owner = register_user_and_login(prefix="owner")
        victim = data_manager.add_user(
            "victim", "v@example.com", "Victim",
            generate_password_hash("pw")
        )
        response = client.post(
            f"/users/edit/{victim.id}",
            data={
                "username": "hacker",
                "email": "hack@evil.com",
                "first_name": "Evil",
                "last_name": "Hacker",
                "age": "99",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Access forbidden" in response.data

    def test_delete_user_valid(self, register_user_and_login, client, data_manager):
        """
        Should delete own user account successfully.
        """
        user = register_user_and_login(prefix="deleteuser")
        user_obj = data_manager.get_user_by_username(user['username'])
        response = client.post(f"/users/delete/{user_obj.id}", follow_redirects=True)
        assert response.status_code == 200
        assert b"deleted" in response.data

    def test_delete_user_invalid(self, register_user_and_login, client, data_manager):
        """
        Should forbid deleting another user's account.
        """
        owner = register_user_and_login(prefix="owner")
        target = data_manager.add_user(
            "target", "target@example.com", "Target",
            generate_password_hash("x")
        )
        response = client.post(f"/users/delete/{target.id}", follow_redirects=True)
        assert response.status_code == 200
        assert b"Access forbidden" in response.data


@pytest.mark.usefixtures("client", "register_user_and_login")
class TestPasswordChange:
    """
    Test password change functionality, covering valid and invalid cases and access control.
    """

    def test_change_password_valid(self, register_user_and_login, client):
        """
        Should update password when current password matches and new passwords align.
        """
        user = register_user_and_login(prefix="changepw")
        user_obj = client.application.data_manager.get_user_by_username(user['username'])
        response = client.post(
            f"/users/{user_obj.id}/change_password",
            data={
                "current_password": user['password'],
                "new_password": "newpass123",
                "confirm_password": "newpass123",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Password updated successfully" in response.data

    @pytest.mark.parametrize(
        "current_pw,new_pw,confirm_pw,error_msg",
        [
            ("wrongpass", "new", "new", b"Current password is incorrect"),
            ("secret123", "new", "different", b"do not match"),
            ("secret123", "secret123", "secret123", b"must differ from current password"),
        ],
    )
    def test_change_password_invalid(self, register_user_and_login, client, current_pw, new_pw, confirm_pw, error_msg):
        """
        Should display appropriate error messages when password change inputs are invalid.
        """
        user = register_user_and_login(prefix="pwtest")
        user_obj = client.application.data_manager.get_user_by_username(user['username'])
        response = client.post(
            f"/users/{user_obj.id}/change_password",
            data={
                "current_password": current_pw,
                "new_password": new_pw,
                "confirm_password": confirm_pw,
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert error_msg in response.data

    def test_change_password_unauthorized(self, register_user_and_login, client, data_manager):
        """
        Should forbid changing password of another user.
        """
        user1 = register_user_and_login(prefix="one")
        user2 = data_manager.add_user(
            "two", "two@example.com", "Two", generate_password_hash("pw")
        )
        response = client.post(
            f"/users/{user2.id}/change_password",
            data={
                "current_password": "pw",
                "new_password": "newpw",
                "confirm_password": "newpw",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Access forbidden" in response.data
