import pytest

# --- Constants used in response content checks ---
APP_TITLE = b"MovieMatrix"
USERS_HEADING = b"Users"
ADD_USER_BUTTON = b"Add User"
MOVIE_TABLE_HEADER = b"Title"


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
    assert b"Please enter a valid username" in response.data


def test_delete_user_valid(client):
    pass


def test_delete_user_invalid(client):
    pass


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
