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


def test_user_movies_page(client):
    """Test that a user's movie page loads correctly and shows their movie list."""
    # Create a user with a unique name
    username = f"MovieUser_{uuid.uuid4().hex[:6]}"
    client.post("/add_user", data={"name": username}, follow_redirects=True)

    # Fetch /users page to extract the user ID
    response = client.get("/users")
    soup = BeautifulSoup(response.data, "html.parser")
    user_row = next((row for row in soup.find_all("tr") if username in row.text), None)
    assert user_row is not None

    user_id = user_row.find("a", {"href": lambda x: x and "/users/" in x})["href"].split("/")[-1]

    # Request the user movies page
    movie_page = client.get(f"/users/{user_id}")
    assert movie_page.status_code == 200

    # Verify that the user's name appears on the page
    assert bytes(username, "utf-8") in movie_page.data


def test_add_movie_valid(client):
    """Test that a valid movie title is fetched via OMDb and added to a user's list."""
    username = f"MovieAdder_{uuid.uuid4().hex[:6]}"
    client.post("/add_user", data={"name": username}, follow_redirects=True)

    # Extract user ID
    response = client.get("/users")
    soup = BeautifulSoup(response.data, "html.parser")
    user_row = next((row for row in soup.find_all("tr") if username in row.text), None)
    assert user_row is not None
    user_id = user_row.find("a", {"href": lambda x: x and "/users/" in x})["href"].split("/")[-1]

    # Use a valid movie title known to OMDb
    response = client.post(
        f"/users/{user_id}/add_movie",
        data={"title": "Inception", "year": "2010"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Inception" in response.data


def test_add_movie_invalid(client):
    """Test that a non-existent movie title is rejected and not added."""
    username = f"OMDbFailUser_{uuid.uuid4().hex[:6]}"
    client.post("/add_user", data={"name": username}, follow_redirects=True)

    # Extract user ID
    response = client.get("/users")
    soup = BeautifulSoup(response.data, "html.parser")
    user_row = next((row for row in soup.find_all("tr") if username in row.text), None)
    assert user_row is not None
    user_id = user_row.find("a", {"href": lambda x: x and "/users/" in x})["href"].split("/")[-1]

    # Submit nonsense movie title
    response = client.post(
        f"/users/{user_id}/add_movie",
        data={"title": "DefinitelyNotARealMovie123456", "year": "2024"},
        follow_redirects=True
    )
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    alert = soup.find("div", class_="alert")
    assert alert is not None
    assert "no movie found" in alert.text.lower()


def test_update_movie_valid(client):
    """Test updating a movie's data after it's added to a user."""
    username = f"UpdateUser_{uuid.uuid4().hex[:6]}"
    original_title = "Inception"
    updated_title = "Inception Updated"

    # Step 1: Create a user
    client.post("/add_user", data={"name": username}, follow_redirects=True)

    # Step 2: Get user ID
    response = client.get("/users")
    soup = BeautifulSoup(response.data, "html.parser")
    user_row = next((r for r in soup.find_all("tr") if username in r.text), None)
    user_id = user_row.find("a", href=True)["href"].split("/")[-1]

    # Step 3: Add movie via OMDb (title + year)
    client.post(
        f"/users/{user_id}/add_movie",
        data={"title": original_title, "year": "2010"},
        follow_redirects=True
    )

    # Step 4: Get movie ID from /users/<user_id>
    movie_list = client.get(f"/users/{user_id}")
    soup = BeautifulSoup(movie_list.data, "html.parser")
    movie_row = next((r for r in soup.find_all("tr") if original_title in r.text), None)
    assert movie_row is not None
    movie_id = movie_row.find("a", href=lambda x: x and "/update_movie/" in x)["href"].split("/")[-1]

    # Step 5: Submit update
    update_response = client.post(
        f"/users/{user_id}/update_movie/{movie_id}",
        data={
            "title": updated_title,
            "director": "Nolan",
            "year": "2010",
            "rating": "9.0"
        },
        follow_redirects=True
    )
    assert update_response.status_code == 200
    assert bytes(updated_title, "utf-8") in update_response.data


def test_update_movie_invalid(client):
    """Test that updating a movie with invalid data fails and shows validation feedback."""
    username = f"InvalidUpdateUser_{uuid.uuid4().hex[:6]}"
    movie_title = "Interstellar"

    # Create a user
    client.post("/add_user", data={"name": username}, follow_redirects=True)

    # Extract user ID
    response = client.get("/users")
    soup = BeautifulSoup(response.data, "html.parser")
    user_row = next((r for r in soup.find_all("tr") if username in r.text), None)
    user_id = user_row.find("a", href=True)["href"].split("/")[-1]

    # Add a movie for the user
    client.post(
        f"/users/{user_id}/add_movie",
        data={"title": movie_title, "year": "2014"},
        follow_redirects=True
    )

    # Get movie ID from user's movie list
    movie_page = client.get(f"/users/{user_id}")
    soup = BeautifulSoup(movie_page.data, "html.parser")
    movie_row = next((r for r in soup.find_all("tr") if movie_title in r.text), None)
    movie_id = movie_row.find("a", href=lambda x: x and "/update_movie/" in x)["href"].split("/")[-1]

    # Submit invalid update (non-numeric year, out-of-range rating)
    update_response = client.post(
        f"/users/{user_id}/update_movie/{movie_id}",
        data={
            "title": "Still Interstellar",
            "director": "Christopher Nolan",
            "year": "twenty",  # invalid year
            "rating": "15"  # invalid rating (too high)
        },
        follow_redirects=True
    )

    assert update_response.status_code == 200

    # Verify that an error message is displayed
    soup = BeautifulSoup(update_response.data, "html.parser")
    alert = soup.find("div", class_="alert")
    assert alert is not None
    assert "valid year" in alert.text.lower() or "valid rating" in alert.text.lower()


def test_delete_movie_valid(client):
    """Test that a movie can be deleted successfully and no longer appears in the user's movie list."""
    username = f"DeleteMovieUser_{uuid.uuid4().hex[:6]}"
    movie_title = "The Matrix"

    # Create user
    client.post("/add_user", data={"name": username}, follow_redirects=True)

    # Extract user ID
    response = client.get("/users")
    soup = BeautifulSoup(response.data, "html.parser")
    user_row = next((r for r in soup.find_all("tr") if username in r.text), None)
    user_id = user_row.find("a", href=True)["href"].split("/")[-1]

    # Add movie
    client.post(
        f"/users/{user_id}/add_movie",
        data={"title": movie_title, "director": "Test", "year": "2020", "rating": "6.5"},
        follow_redirects=True
    )

    # Get user movies page and locate the movie row
    movie_page = client.get(f"/users/{user_id}")
    soup = BeautifulSoup(movie_page.data, "html.parser")
    movie_table = soup.find("table", class_="table")
    movie_row = next((r for r in movie_table.find_all("tr") if movie_title in r.text), None)
    assert movie_row is not None

    # Extract movie ID and delete
    delete_form = movie_row.find("form", {"action": lambda x: x and "delete_movie" in x})
    assert delete_form is not None
    movie_id = delete_form["action"].split("/")[-1]

    delete_response = client.post(
        f"/users/{user_id}/delete_movie/{movie_id}",
        follow_redirects=True
    )
    assert delete_response.status_code == 200

    # Check that movie is no longer in the table
    soup = BeautifulSoup(delete_response.data, "html.parser")
    movie_table = soup.find("table", class_="table")
    rows = movie_table.find_all("tr") if movie_table else []
    assert all(movie_title not in row.text for row in rows)


def test_delete_movie_invalid(client):
    """Test that deleting a non-existent movie does not break the app."""
    # Create a user
    username = f"InvalidMovieUser_{uuid.uuid4().hex[:6]}"
    client.post("/add_user", data={"name": username}, follow_redirects=True)

    # Extract user ID
    response = client.get("/users")
    soup = BeautifulSoup(response.data, "html.parser")
    user_row = next((r for r in soup.find_all("tr") if username in r.text), None)
    assert user_row is not None
    user_id = user_row.find("a", href=True)["href"].split("/")[-1]

    # Try to delete a movie with a clearly non-existent ID
    delete_response = client.post(
        f"/users/{user_id}/delete_movie/9999",
        follow_redirects=True
    )
    assert delete_response.status_code == 200

    # Check for a meaningful error message
    soup = BeautifulSoup(delete_response.data, "html.parser")
    alert_box = soup.find("div", class_="alert")
    assert alert_box is not None
    assert "not found" in alert_box.text.lower() or "could not" in alert_box.text.lower()


def test_user_reviews_page(client):
    """Test that the user's reviews page loads successfully and includes added review."""
    username = f"ReviewUser_{uuid.uuid4().hex[:6]}"
    movie_title = "The Matrix"

    # Create user
    client.post("/add_user", data={"name": username}, follow_redirects=True)

    # Get user ID
    response = client.get("/users")
    soup = BeautifulSoup(response.data, "html.parser")
    user_row = next((r for r in soup.find_all("tr") if username in r.text), None)
    user_id = user_row.find("a", href=True)["href"].split("/")[-1]

    # Add a movie
    client.post(
        f"/users/{user_id}/add_movie",
        data={"title": movie_title, "director": "Wachowski", "year": "1999", "rating": "9.0"},
        follow_redirects=True
    )

    # Extract movie ID
    response = client.get(f"/users/{user_id}")
    soup = BeautifulSoup(response.data, "html.parser")
    movie_row = next((r for r in soup.find_all("tr") if movie_title in r.text), None)
    movie_id = movie_row.find("a", {"href": lambda x: x and "/reviews" in x})["href"].split("/")[-2]

    # Add review (corrected route!)
    client.post(
        f"/users/{user_id}/movies/{movie_id}/add_review",
        data={"text": "Amazing movie!", "user_rating": "9.0"},
        follow_redirects=True
    )

    # Request user's reviews page
    response = client.get(f"/users/{user_id}/reviews")
    assert response.status_code == 200
    assert b"Amazing movie!" in response.data


def test_movie_reviews_page(client):
    """Test that the reviews for a movie are shown correctly on the movie reviews page."""
    username = f"MovieReviewUser_{uuid.uuid4().hex[:6]}"
    movie_title = "Inception"
    review_text = "Mind-blowing film."

    # Create user
    client.post("/add_user", data={"name": username}, follow_redirects=True)

    # Get user ID
    response = client.get("/users")
    soup = BeautifulSoup(response.data, "html.parser")
    user_row = next((r for r in soup.find_all("tr") if username in r.text), None)
    user_id = user_row.find("a", href=True)["href"].split("/")[-1]

    # Add movie
    client.post(
        f"/users/{user_id}/add_movie",
        data={"title": movie_title, "director": "Nolan", "year": "2010", "rating": "8.8"},
        follow_redirects=True
    )

    # Extract movie ID
    response = client.get(f"/users/{user_id}")
    soup = BeautifulSoup(response.data, "html.parser")
    movie_row = next((r for r in soup.find_all("tr") if movie_title in r.text), None)
    movie_id = movie_row.find("a", {"href": lambda x: x and "/reviews" in x})["href"].split("/")[-2]

    # Add review
    client.post(
        f"/users/{user_id}/movies/{movie_id}/add_review",
        data={"text": review_text, "user_rating": "9.0"},
        follow_redirects=True
    )

    # Load movie reviews page
    response = client.get(f"/movies/{movie_id}/reviews?user_id={user_id}")
    assert response.status_code == 200
    assert bytes(review_text, "utf-8") in response.data


def test_add_review_valid(client):
    """Test that a valid review can be added and is visible on the movie reviews page."""
    username = f"ReviewValidUser_{uuid.uuid4().hex[:6]}"
    movie_title = "Interstellar"
    review_text = "Fantastic visuals and storytelling."

    # Add user
    client.post("/add_user", data={"name": username}, follow_redirects=True)

    # Extract user ID
    response = client.get("/users")
    soup = BeautifulSoup(response.data, "html.parser")
    user_row = next((r for r in soup.find_all("tr") if username in r.text), None)
    user_id = user_row.find("a", href=True)["href"].split("/")[-1]

    # Add movie
    client.post(
        f"/users/{user_id}/add_movie",
        data={"title": movie_title, "director": "Christopher Nolan", "year": "2014", "rating": "8.6"},
        follow_redirects=True
    )

    # Get movie ID
    response = client.get(f"/users/{user_id}")
    soup = BeautifulSoup(response.data, "html.parser")
    movie_row = next((r for r in soup.find_all("tr") if movie_title in r.text), None)
    movie_id = movie_row.find("a", {"href": lambda x: x and "/reviews" in x})["href"].split("/")[-2]

    # Add review
    post_review = client.post(
        f"/users/{user_id}/movies/{movie_id}/add_review",
        data={"text": review_text, "user_rating": "9.5"},
        follow_redirects=True
    )
    assert post_review.status_code == 200

    # Confirm review appears on movie reviews page
    response = client.get(f"/movies/{movie_id}/reviews?user_id={user_id}")
    assert response.status_code == 200
    assert bytes(review_text, "utf-8") in response.data


@pytest.mark.parametrize("text,rating", [
    ("", "8.5"),  # Missing review text
    ("Nice movie", ""),  # Missing rating
    ("Nice movie", "eleven"),  # Invalid non-numeric rating
    ("Nice movie", "11.0"),  # Out-of-range rating
])
def test_add_review_invalid(client, text, rating):
    """Test that invalid reviews are rejected and not shown."""
    username = f"ReviewInvalidUser_{uuid.uuid4().hex[:6]}"
    movie_title = "Inception"

    # Create user
    client.post("/add_user", data={"name": username}, follow_redirects=True)

    # Extract user ID
    response = client.get("/users")
    soup = BeautifulSoup(response.data, "html.parser")
    user_row = next((r for r in soup.find_all("tr") if username in r.text), None)
    user_id = user_row.find("a", href=True)["href"].split("/")[-1]

    # Add movie
    client.post(
        f"/users/{user_id}/add_movie",
        data={"title": movie_title, "director": "Christopher Nolan", "year": "2010", "rating": "9.0"},
        follow_redirects=True
    )

    # Get movie ID
    response = client.get(f"/users/{user_id}")
    soup = BeautifulSoup(response.data, "html.parser")
    movie_row = next((r for r in soup.find_all("tr") if movie_title in r.text), None)
    movie_id = movie_row.find("a", {"href": lambda x: x and "/reviews" in x})["href"].split("/")[-2]

    # Attempt to post invalid review
    response = client.post(
        f"/users/{user_id}/movies/{movie_id}/add_review",
        data={"text": text, "user_rating": rating},
        follow_redirects=True
    )

    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    alert = soup.find("div", class_="alert")
    assert alert is not None
    assert "review text cannot be empty" in alert.text.lower() \
           or "invalid" in alert.text.lower() \
           or "please enter" in alert.text.lower()


def test_edit_review_valid(client):
    pass


def test_edit_review_invalid(client):
    pass


def test_delete_review_valid(client):
    pass


def test_delete_review_invalid(client):
    pass
