import uuid
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from werkzeug.security import generate_password_hash

# --- Constants used in response content checks ---
APP_TITLE = b"MovieMatrix"
USERS_HEADING = b"Users"
ADD_USER_BUTTON = b"Add User"
INVALID_USERNAME_MSG = b"Please enter a valid username"


# ---------------------- HOME PAGE ---------------------- #

def test_home_page(client):
    """
    Should load the home page and contain the app title.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert APP_TITLE in response.data


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


def test_login_and_logout_flow(client, data_manager):
    """
    Should allow a user to log in and log out successfully.
    """
    # Setup user manually
    user = data_manager.add_user(
        username="loginuser",
        email="login@example.com",
        first_name="Test",
        password_hash="pbkdf2:sha256:260000$test$hashedvalue123",  # won't match password
    )

    # Wrong password
    res_fail = client.post("/login", data={
        "username": "loginuser",
        "password": "wrongpass"
    }, follow_redirects=True)
    assert b"Invalid username or password." in res_fail.data

    # Update to known hash
    from werkzeug.security import generate_password_hash
    data_manager.update_user(user.id, {"password_hash": generate_password_hash("correctpass")})

    # Correct login
    res_login = client.post("/login", data={
        "username": "loginuser",
        "password": "correctpass"
    }, follow_redirects=True)
    assert b"Welcome" in res_login.data

    # Logout
    res_logout = client.get("/logout", follow_redirects=True)
    assert b"You have been logged out." in res_logout.data


# ---------------------- Users -------------------------- #

def test_list_users(client):
    """
    Should load the users list page and include expected UI elements.
    """
    response = client.get("/users")
    assert response.status_code == 200
    assert b"Users" in response.data
    assert b"Add User" in response.data


def test_add_user_valid(client):
    """
    Should allow creation of a valid user.
    """
    username = f"User_{uuid.uuid4().hex[:6]}"
    response = client.post("/add_user", data={
        "username": username,
        "email": f"{username}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "age": "28",
        "password": "password123",
        "confirm_password": "password123"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert bytes(username, "utf-8") in response.data
    assert b"created" in response.data


@pytest.mark.parametrize("field,value,error_message", [
    ("username", "", b"Invalid username"),
    ("email", "invalid@", b"Invalid e-mail"),
    ("first_name", "!!", b"First name"),
    ("password", "", b"Passwords do not match"),
    ("confirm_password", "wrong", b"Passwords do not match"),
])
def test_add_user_invalid_input(client, field, value, error_message):
    """
    Should reject user creation with invalid input fields.
    """
    form = {
        "username": "validuser",
        "email": "user@example.com",
        "first_name": "Valid",
        "last_name": "Name",
        "age": "30",
        "password": "pass123",
        "confirm_password": "pass123"
    }
    form[field] = value

    response = client.post("/add_user", data=form, follow_redirects=True)
    assert response.status_code == 200
    assert error_message in response.data


def test_update_user_valid(client, data_manager):
    """
    Should allow a logged-in user to update their profile.
    """
    # Setup: Create and login user
    user = data_manager.add_user(
        "updateuser", "update@example.com", "Update", generate_password_hash("pass123")
    )
    client.post("/login", data={"username": "updateuser", "password": "pass123"}, follow_redirects=True)

    response = client.post(f"/update_user/{user.id}", data={
        "username": "updateuser",
        "email": "updated@example.com",
        "first_name": "Updated",
        "last_name": "Name",
        "age": "35"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"User updated." in response.data


def test_delete_user_valid(client, data_manager):
    """
    Should delete the user and redirect to /users.
    """
    user = data_manager.add_user(
        "deleteuser", "delete@example.com", "Del", generate_password_hash("delpass")
    )
    client.post("/login", data={"username": "deleteuser", "password": "delpass"}, follow_redirects=True)

    response = client.post(f"/delete_user/{user.id}", follow_redirects=True)
    assert response.status_code == 200
    assert b"deleted" in response.data


def test_change_password_valid(client, data_manager):
    """
    Should change the user password if current password matches.
    """
    user = data_manager.add_user(
        "changepw", "pw@example.com", "PW", generate_password_hash("oldpass")
    )
    client.post("/login", data={"username": "changepw", "password": "oldpass"}, follow_redirects=True)

    response = client.post(f"/users/{user.id}/change_password", data={
        "current_password": "oldpass",
        "new_password": "newpass123",
        "confirm_password": "newpass123"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Password updated successfully" in response.data


@pytest.mark.parametrize("current_pw,new_pw,confirm_pw,error_msg", [
    ("wrongpass", "new", "new", b"Current password is incorrect"),
    ("oldpass", "new", "different", b"do not match"),
    ("oldpass", "oldpass", "oldpass", b"must be different"),
])
def test_change_password_invalid(client, data_manager, current_pw, new_pw, confirm_pw, error_msg):
    """
    Should reject invalid password change scenarios.
    """
    import uuid
    unique = uuid.uuid4().hex[:6]
    user = data_manager.add_user(
        f"failpw_{unique}",
        f"fail_{unique}@example.com",
        "Fail",
        generate_password_hash("oldpass")
    )
    assert user is not None, "User creation failed in test setup"

    client.post("/login", data={"username": f"failpw_{unique}", "password": "oldpass"}, follow_redirects=True)

    response = client.post(f"/users/{user.id}/change_password", data={
        "current_password": current_pw,
        "new_password": new_pw,
        "confirm_password": confirm_pw
    }, follow_redirects=True)

    assert response.status_code == 200
    assert error_msg in response.data


# ---------------------- Movie -------------------------- #

def create_user_and_login(client, data_manager):
    import uuid
    unique = uuid.uuid4().hex[:6]
    username = f"user_{unique}"
    email = f"{username}@test.com"
    password = "secret123"

    user = data_manager.add_user(username, email, "Movie", password_hash=generate_password_hash(password))
    assert user is not None
    client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
    return user


def test_movies_page(client):
    """
    Should load all movies page (even if empty).
    """
    response = client.get("/movies")
    assert response.status_code == 200
    assert b"Movies" in response.data


def test_add_movie_valid(client, data_manager):
    """
    Should add a movie to the user list using valid OMDb data.
    """
    user = create_user_and_login(client, data_manager)

    response = client.post(
        f"/users/{user.id}/add_movie",
        data={"title": "Inception", "year": "2010", "planned": "on"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Inception" in response.data
    assert b"added" in response.data


def test_add_movie_invalid(client, data_manager):
    """
    Should not add a movie with non-existent OMDb data.
    """
    user = create_user_and_login(client, data_manager)

    response = client.post(
        f"/users/{user.id}/add_movie",
        data={"title": "SomeFakeTitleThatDoesNotExist_9999"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"No movie found." in response.data


def test_user_movies_page(client, data_manager):
    """
    Should show the user's movie list after adding a movie.
    """
    user = create_user_and_login(client, data_manager)

    # Add movie
    client.post(
        f"/users/{user.id}/add_movie",
        data={"title": "Interstellar", "year": "2014", "watched": "on"},
        follow_redirects=True
    )

    response = client.get(f"/users/{user.id}")
    assert response.status_code == 200
    assert b"Interstellar" in response.data


def test_update_movie_valid(client, data_manager):
    """
    Should update a movie's metadata for a user.
    """
    user = create_user_and_login(client, data_manager)

    # Add movie
    client.post(
        f"/users/{user.id}/add_movie",
        data={"title": "Blade Runner", "year": "1982"},
        follow_redirects=True
    )

    # Extract movie ID
    page = client.get(f"/users/{user.id}")
    soup = BeautifulSoup(page.data, "html.parser")
    movie_row = next((r for r in soup.find_all("tr") if "Blade Runner" in r.text), None)
    assert movie_row is not None, "Movie row not found for 'Blade Runner'"

    movie_id = movie_row.find("a", href=lambda x: x and "update_movie" in x)["href"].split("/")[-1]

    # Submit update
    response = client.post(
        f"/users/{user.id}/update_movie/{movie_id}",
        data={
            "title": "Blade Runner Final",
            "director": "Ridley Scott",
            "year": "1982",
            "imdb_rating": "8.5"
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Blade Runner Final" in response.data


def test_update_movie_invalid_data(client, data_manager):
    """
    Should reject invalid movie metadata (bad year or rating).
    """
    user = create_user_and_login(client, data_manager)

    client.post(
        f"/users/{user.id}/add_movie",
        data={"title": "Dune", "year": "2021"},
        follow_redirects=True
    )

    page = client.get(f"/users/{user.id}")
    soup = BeautifulSoup(page.data, "html.parser")
    movie_row = next((r for r in soup.find_all("tr") if "Dune" in r.text), None)
    assert movie_row is not None, "Movie row not found for 'Dune'"

    movie_id = movie_row.find("a", href=lambda x: x and "update_movie" in x)["href"].split("/")[-1]

    response = client.post(
        f"/users/{user.id}/update_movie/{movie_id}",
        data={
            "title": "Dune",
            "director": "Villeneuve",
            "year": "two thousand",  # invalid year
            "imdb_rating": "11.0"  # out-of-range rating
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Invalid year" in response.data or b"IMDb rating must be" in response.data


def test_delete_movie_valid(client, data_manager):
    """
    Should delete a movie from the user's list.
    """
    user = create_user_and_login(client, data_manager)

    client.post(
        f"/users/{user.id}/add_movie",
        data={"title": "Tenet", "year": "2020"},
        follow_redirects=True
    )

    page = client.get(f"/users/{user.id}")
    soup = BeautifulSoup(page.data, "html.parser")
    movie_row = next((r for r in soup.find_all("tr") if "Tenet" in r.text), None)
    assert movie_row is not None, "Movie row not found for 'Tenet'"

    delete_form = movie_row.find("form", {"action": lambda x: x and "delete_movie" in x})
    assert delete_form is not None
    movie_id = delete_form["action"].split("/")[-1]

    response = client.post(
        f"/users/{user.id}/delete_movie/{movie_id}",
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"deleted" in response.data
    assert b"Tenet" not in response.data


def test_delete_movie_invalid(client, data_manager):
    """
    Should gracefully handle deleting a non-existent movie.
    """
    user = create_user_and_login(client, data_manager)

    response = client.post(f"/users/{user.id}/delete_movie/999999", follow_redirects=True)
    assert response.status_code == 200
    assert b"Movie not found" in response.data


# ---------------------- Review -------------------------- #

def test_user_reviews_page(client, data_manager):
    """
    Should show all reviews written by the user.
    """
    user = create_user_and_login(client, data_manager)

    # Add movie
    client.post(
        f"/users/{user.id}/add_movie",
        data={"title": "Arrival", "year": "2016"},
        follow_redirects=True
    )

    # Get movie_id from existing "Reviews" link
    page = client.get(f"/users/{user.id}")
    soup = BeautifulSoup(page.data, "html.parser")
    review_link = soup.find("a", href=lambda x: x and "/movies/" in x and "/reviews" in x)
    assert review_link is not None, "Could not find Reviews link"
    movie_id = review_link["href"].split("/")[2]

    # Add review
    client.post(
        f"/users/{user.id}/movies/{movie_id}/add_review",
        data={"title": "Stunning", "text": "Loved it!", "user_rating": "8.5"},
        follow_redirects=True
    )

    # Verify review appears on user's review page
    response = client.get(f"/users/{user.id}/reviews")
    assert response.status_code == 200
    assert b"Stunning" in response.data


def test_movie_reviews_page(client, data_manager):
    """
    Should display reviews for a given movie.
    """
    user = create_user_and_login(client, data_manager)

    client.post(
        f"/users/{user.id}/add_movie",
        data={"title": "The Prestige", "year": "2006"},
        follow_redirects=True
    )

    # Extract movie_id from review button
    page = client.get(f"/users/{user.id}")
    soup = BeautifulSoup(page.data, "html.parser")
    review_link = soup.find("a", href=lambda x: x and "/movies/" in x and "/reviews" in x)
    assert review_link is not None
    movie_id = review_link["href"].split("/")[2]

    # Add review
    client.post(
        f"/users/{user.id}/movies/{movie_id}/add_review",
        data={"title": "Twisty", "text": "Great plot!", "user_rating": "9.0"},
        follow_redirects=True
    )

    # View movie reviews page
    response = client.get(f"/movies/{movie_id}/reviews")
    assert response.status_code == 200
    assert b"Twisty" in response.data


def test_add_review_invalid(client, data_manager):
    """
    Should reject invalid review input (missing fields or invalid rating).
    """
    user = create_user_and_login(client, data_manager)

    client.post(
        f"/users/{user.id}/add_movie",
        data={"title": "Gravity", "year": "2013"},
        follow_redirects=True
    )

    page = client.get(f"/users/{user.id}")
    soup = BeautifulSoup(page.data, "html.parser")
    review_link = soup.find("a", href=lambda x: x and "/movies/" in x and "/reviews" in x)
    assert review_link is not None
    movie_id = review_link["href"].split("/")[2]

    response = client.post(
        f"/users/{user.id}/movies/{movie_id}/add_review",
        data={"title": "", "text": "", "user_rating": "eleven"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"required" in response.data or b"invalid" in response.data


def test_edit_review_valid(client, data_manager):
    """
    Should allow editing a valid review.
    """
    user = create_user_and_login(client, data_manager)

    client.post(
        f"/users/{user.id}/add_movie",
        data={"title": "Looper", "year": "2012"},
        follow_redirects=True
    )

    page = client.get(f"/users/{user.id}")
    soup = BeautifulSoup(page.data, "html.parser")
    review_link = soup.find("a", href=lambda x: x and "/movies/" in x and "/reviews" in x)
    assert review_link is not None
    movie_id = review_link["href"].split("/")[2]

    client.post(
        f"/users/{user.id}/movies/{movie_id}/add_review",
        data={"title": "Solid", "text": "Cool time-travel", "user_rating": "7.5"},
        follow_redirects=True
    )

    page = client.get(f"/users/{user.id}/reviews")
    soup = BeautifulSoup(page.data, "html.parser")
    review_row = next((r for r in soup.find_all("tr") if "Solid" in r.text), None)
    assert review_row is not None
    review_id = review_row.find("form")["action"].split("/")[-1]

    edit_response = client.post(
        f"/users/{user.id}/edit_review/{review_id}",
        data={"title": "Improved", "text": "Updated thoughts", "user_rating": "8.0"},
        follow_redirects=True
    )

    assert edit_response.status_code == 200
    assert b"Improved" in edit_response.data


def test_delete_review_valid(client, data_manager):
    """
    Should delete a review and remove it from the user list.
    """
    user = create_user_and_login(client, data_manager)

    client.post(
        f"/users/{user.id}/add_movie",
        data={"title": "Her", "year": "2013"},
        follow_redirects=True
    )

    page = client.get(f"/users/{user.id}")
    soup = BeautifulSoup(page.data, "html.parser")
    review_link = soup.find("a", href=lambda x: x and "/movies/" in x and "/reviews" in x)
    assert review_link is not None
    movie_id = review_link["href"].split("/")[2]

    client.post(
        f"/users/{user.id}/movies/{movie_id}/add_review",
        data={"title": "Emotional", "text": "Loved the tone", "user_rating": "9.0"},
        follow_redirects=True
    )

    page = client.get(f"/users/{user.id}/reviews")
    soup = BeautifulSoup(page.data, "html.parser")
    review_row = next((r for r in soup.find_all("tr") if "Emotional" in r.text), None)
    assert review_row is not None
    review_id = review_row.find("form")["action"].split("/")[-1]

    delete_response = client.post(
        f"/users/{user.id}/delete_review/{review_id}",
        follow_redirects=True
    )

    assert delete_response.status_code == 200
    assert b"Emotional" not in delete_response.data


def test_review_detail_page(client, data_manager):
    """
    Should show review details for public display.
    """
    user = create_user_and_login(client, data_manager)

    client.post(
        f"/users/{user.id}/add_movie",
        data={"title": "The Martian", "year": "2015"},
        follow_redirects=True
    )

    page = client.get(f"/users/{user.id}")
    soup = BeautifulSoup(page.data, "html.parser")
    review_link = soup.find("a", href=lambda x: x and "/movies/" in x and "/reviews" in x)
    assert review_link is not None
    movie_id = review_link["href"].split("/")[2]

    client.post(
        f"/users/{user.id}/movies/{movie_id}/add_review",
        data={"title": "Funny", "text": "Great humor", "user_rating": "8.5"},
        follow_redirects=True
    )

    page = client.get(f"/users/{user.id}/reviews")
    soup = BeautifulSoup(page.data, "html.parser")
    review_row = next((r for r in soup.find_all("tr") if "Funny" in r.text), None)
    assert review_row is not None
    review_id = review_row.find("form")["action"].split("/")[-1]

    detail = client.get(f"/users/{user.id}/review/{review_id}")
    assert detail.status_code == 200
    assert b"Great humor" in detail.data


# ---------------------- Password -------------------------- #

def test_change_password_valid(client, data_manager):
    """
    Should allow a user to change password successfully.
    """
    user = data_manager.add_user(
        "changepw", "change@example.com", "Change", generate_password_hash("oldpass")
    )
    client.post("/login", data={"username": "changepw", "password": "oldpass"}, follow_redirects=True)

    response = client.post(
        f"/users/{user.id}/change_password",
        data={
            "current_password": "oldpass",
            "new_password": "newsecure",
            "confirm_password": "newsecure"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Password updated successfully" in response.data


@pytest.mark.parametrize("current_pw,new_pw,confirm_pw,error_msg", [
    ("wrongpass", "new", "new", b"Current password is incorrect"),
    ("oldpass", "new", "different", b"do not match"),
    ("oldpass", "oldpass", "oldpass", b"must be different"),
])
def test_change_password_invalid(client, data_manager, current_pw, new_pw, confirm_pw, error_msg):
    """
    Should reject invalid password change scenarios.
    """
    import uuid
    unique = uuid.uuid4().hex[:6]
    user = data_manager.add_user(
        f"failpw_{unique}",
        f"fail_{unique}@example.com",
        "Fail",
        generate_password_hash("oldpass")
    )
    client.post("/login", data={"username": user.username, "password": "oldpass"}, follow_redirects=True)

    response = client.post(
        f"/users/{user.id}/change_password",
        data={
            "current_password": current_pw,
            "new_password": new_pw,
            "confirm_password": confirm_pw
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert error_msg in response.data


# ---------------------- Error-Handling -------------------------- #

def test_forbidden_access_to_other_user_movies(client, data_manager):
    """
    Should redirect with a flash message when accessing another user's movies.
    """
    # User A
    user1 = data_manager.add_user(
        "user403a", "403a@example.com", "UserA", generate_password_hash("pass")
    )
    # User B
    user2 = data_manager.add_user(
        "user403b", "403b@example.com", "UserB", generate_password_hash("pass")
    )

    # Log in as user1
    client.post("/login", data={"username": user1.username, "password": "pass"}, follow_redirects=True)

    # Try to access user2's movie page
    response = client.get(f"/users/{user2.id}", follow_redirects=True)

    assert response.status_code == 200
    assert b"You are not allowed to access this resource." in response.data


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
    with patch("app.data_manager.get_all_users", side_effect=Exception("Boom")):
        response = client.get("/users", follow_redirects=True)

    assert response.status_code == 500
    assert b"500" in response.data or b"internal" in response.data.lower()


# ---------------------- Login -------------------------- #

def test_login_valid(client, data_manager):
    """
    Should log the user in and redirect to user list.
    """
    username = f"login_{uuid.uuid4().hex[:6]}"
    email = f"{username}@example.com"

    data_manager.add_user(username, email, "Login", generate_password_hash("secure123"))

    response = client.post("/login", data={"username": username, "password": "secure123"}, follow_redirects=True)

    assert response.status_code == 200
    assert b"Welcome" in response.data


def test_login_invalid(client):
    """
    Should reject wrong username or password.
    """
    response = client.post("/login", data={"username": "fakeuser", "password": "wrongpass"}, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid username or password." in response.data


def test_logout(client, data_manager):
    """
    Should log out the user and redirect to login page.
    """
    data_manager.add_user("logoutuser", "logout@example.com", "Out", generate_password_hash("bye123"))

    client.post("/login", data={"username": "logoutuser", "password": "bye123"}, follow_redirects=True)
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
