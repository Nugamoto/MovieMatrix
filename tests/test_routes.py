import uuid

import pytest
from bs4 import BeautifulSoup

# --- Constants used in response content checks ---
APP_TITLE = b"MovieMatrix"
USERS_HEADING = b"Users"
ADD_USER_BUTTON = b"Add User"
INVALID_USERNAME_MSG = b"Please enter a valid username"


def test_home_page(client):
    """Test that the home page loads and shows the app title."""
    response = client.get("/")
    assert response.status_code == 200
    assert APP_TITLE in response.data


def test_users_page(client):
    """Test that the users page loads and contains the users header."""
    response = client.get("/users")
    assert response.status_code == 200
    assert USERS_HEADING in response.data
    assert ADD_USER_BUTTON in response.data


def test_add_user_valid(client):
    """Test adding a new user via POST with valid data."""
    response = client.post("/add_user", data={"name": "TestUser"}, follow_redirects=True)
    assert response.status_code == 200
    assert USERS_HEADING in response.data
    assert b"TestUser" in response.data


@pytest.mark.parametrize("invalid_name", ["", "   ", "$$!@#"])
def test_add_user_invalid(client, invalid_name):
    """Test that invalid usernames are rejected by the form validation."""
    response = client.post("/add_user", data={"name": invalid_name}, follow_redirects=True)
    assert response.status_code == 200
    assert INVALID_USERNAME_MSG in response.data


def test_delete_user_valid(client):
    """Test that an existing user can be deleted successfully and is removed from the user table."""
    unique_name = f"ToBeDeleted_{uuid.uuid4().hex[:8]}"
    client.post("/add_user", data={"name": unique_name}, follow_redirects=True)

    # Get /users page and find the row with the test user
    response = client.get("/users")
    soup = BeautifulSoup(response.data, "html.parser")
    matching_row = next((row for row in soup.find_all("tr") if unique_name in row.text), None)
    assert matching_row is not None

    # Get the delete form and extract user_id
    delete_form = matching_row.find("form", {"action": lambda x: x and "delete_user" in x})
    assert delete_form is not None
    user_id = delete_form["action"].split("/")[-1]

    # Submit the deletion and verify user is no longer in table
    delete_response = client.post(f"/delete_user/{user_id}", follow_redirects=True)
    assert delete_response.status_code == 200
    soup = BeautifulSoup(delete_response.data, "html.parser")
    remaining_rows = soup.find_all("tr")
    assert all(unique_name not in row.text for row in remaining_rows)


def test_delete_user_invalid(client):
    """Test that deleting a non-existent user does not break the app."""
    response = client.post("/delete_user/9999", follow_redirects=True)
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    alert_box = soup.find("div", class_="alert")
    assert alert_box is not None
    assert "not found" in alert_box.text.lower() or "could not" in alert_box.text.lower()


# --- Placeholder tests for future implementation ---

def test_user_movies_page(client):
    pass


def test_add_movie_valid(client):
    pass


def test_add_movie_invalid(client):
    pass


def test_update_movie_valid(client):
    pass


def test_update_movie_invalid(client):
    pass


def test_delete_movie_valid(client):
    pass


def test_delete_movie_invalid(client):
    pass


def test_user_reviews_page(client):
    pass


def test_movie_reviews_page(client):
    pass


def test_add_review_valid(client):
    pass


def test_add_review_invalid(client):
    pass


def test_edit_review_valid(client):
    pass


def test_edit_review_invalid(client):
    pass


def test_delete_review_valid(client):
    pass


def test_delete_review_invalid(client):
    pass
