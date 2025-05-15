import uuid
from unittest.mock import patch

from bs4 import BeautifulSoup
from werkzeug.security import generate_password_hash


# ---------------------- Helpers -------------------------- #

def create_user_and_login(client, data_manager):
    """Create a test user and log them in."""
    unique = uuid.uuid4().hex[:6]
    username = f"user_{unique}"
    email = f"{username}@test.com"
    password = "secret123"
    user = data_manager.add_user(username, email, "Review", password_hash=generate_password_hash(password))
    client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
    return user


def add_movie(client, user, mock_fetch):
    """Add a movie using a mocked OMDb response and return its ID from the DB directly."""
    mock_fetch.return_value = {
        "title": "Arrival",
        "year": "2016",
        "director": "Denis Villeneuve",
        "genre": "Sci-Fi",
        "poster_url": "",
        "imdb_rating": "8.0",
    }

    client.post(
        f"/movies/add/{user.id}",
        data={"title": "Arrival", "year": "2016"},
        follow_redirects=True
    )

    # Direct DB access: get movie by user
    movies = client.application.data_manager.get_movies_by_user(user.id)
    assert movies, "No movies found for user"
    return movies[0].id


# ---------------------- Review Tests -------------------------- #

@patch("blueprints.movies.fetch_movie")
def test_user_reviews_page(mock_fetch, client, data_manager):
    user = create_user_and_login(client, data_manager)
    movie_id = add_movie(client, user, mock_fetch)

    client.post(f"/reviews/user/{user.id}/movie/{movie_id}/add", data={
        "title": "Stunning",
        "text": "Loved it!",
        "user_rating": "8.5"
    }, follow_redirects=True)

    response = client.get(f"/reviews/user/{user.id}")
    assert response.status_code == 200
    assert b"Stunning" in response.data


@patch("blueprints.movies.fetch_movie")
def test_movie_reviews_page(mock_fetch, client, data_manager):
    user = create_user_and_login(client, data_manager)
    movie_id = add_movie(client, user, mock_fetch)

    client.post(f"/reviews/user/{user.id}/movie/{movie_id}/add", data={
        "title": "Twisty",
        "text": "Great plot!",
        "user_rating": "9.0"
    }, follow_redirects=True)

    response = client.get(f"/reviews/movie/{movie_id}")
    assert response.status_code == 200
    assert b"Twisty" in response.data


@patch("blueprints.movies.fetch_movie")
def test_review_detail_page(mock_fetch, client, data_manager):
    user = create_user_and_login(client, data_manager)
    movie_id = add_movie(client, user, mock_fetch)

    client.post(f"/reviews/user/{user.id}/movie/{movie_id}/add", data={
        "title": "Funny",
        "text": "Great humor",
        "user_rating": "8.5"
    }, follow_redirects=True)

    page = client.get(f"/reviews/user/{user.id}")
    soup = BeautifulSoup(page.data, "html.parser")
    review_row = next((r for r in soup.find_all("tr") if "Funny" in r.text), None)
    review_id = review_row.find("form")["action"].split("/")[-1]

    detail = client.get(f"/reviews/user/{user.id}/review/{review_id}")
    assert detail.status_code == 200
    assert b"Great humor" in detail.data


@patch("blueprints.movies.fetch_movie")
def test_add_review_valid(mock_fetch, client, data_manager):
    """Should add a valid review and show success."""
    user = create_user_and_login(client, data_manager)
    movie_id = add_movie(client, user, mock_fetch)

    response = client.post(
        f"/reviews/user/{user.id}/movie/{movie_id}/add",
        data={
            "title": "Masterpiece",
            "text": "A beautiful story with great visuals.",
            "user_rating": "9.0"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Review added" in response.data
    assert b"Masterpiece" in response.data


@patch("blueprints.movies.fetch_movie")
def test_add_review_invalid(mock_fetch, client, data_manager):
    user = create_user_and_login(client, data_manager)
    movie_id = add_movie(client, user, mock_fetch)

    response = client.post(f"/reviews/user/{user.id}/movie/{movie_id}/add", data={
        "title": "",
        "text": "",
        "user_rating": "eleven"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"required" in response.data or b"invalid" in response.data


@patch("blueprints.movies.fetch_movie")
def test_edit_review_valid(mock_fetch, client, data_manager):
    user = create_user_and_login(client, data_manager)
    movie_id = add_movie(client, user, mock_fetch)

    client.post(f"/reviews/user/{user.id}/movie/{movie_id}/add", data={
        "title": "Solid",
        "text": "Cool time-travel",
        "user_rating": "7.5"
    }, follow_redirects=True)

    page = client.get(f"/reviews/user/{user.id}")
    soup = BeautifulSoup(page.data, "html.parser")
    review_row = next((r for r in soup.find_all("tr") if "Solid" in r.text), None)
    review_id = review_row.find("form")["action"].split("/")[-1]

    response = client.post(f"/reviews/user/{user.id}/edit/{review_id}", data={
        "title": "Improved",
        "text": "Updated thoughts",
        "user_rating": "8.0"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Improved" in response.data


@patch("blueprints.movies.fetch_movie")
def test_edit_review_invalid(mock_fetch, client, data_manager):
    """Should reject review update with invalid data."""
    user = create_user_and_login(client, data_manager)
    movie_id = add_movie(client, user, mock_fetch)

    # First: create valid review
    client.post(f"/reviews/user/{user.id}/movie/{movie_id}/add", data={
        "title": "Initial",
        "text": "Thoughts...",
        "user_rating": "7.0"
    }, follow_redirects=True)

    # Then: extract review ID from review list
    page = client.get(f"/reviews/user/{user.id}")
    soup = BeautifulSoup(page.data, "html.parser")
    review_row = next((r for r in soup.find_all("tr") if "Initial" in r.text), None)
    review_id = review_row.find("form")["action"].split("/")[-1]

    # Submit invalid update (empty title & text, bad rating)
    response = client.post(
        f"/reviews/user/{user.id}/edit/{review_id}",
        data={
            "title": "",
            "text": "",
            "user_rating": "12.0"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"required" in response.data or b"Rating must be" in response.data


@patch("blueprints.movies.fetch_movie")
def test_delete_review_valid(mock_fetch, client, data_manager):
    user = create_user_and_login(client, data_manager)
    movie_id = add_movie(client, user, mock_fetch)

    client.post(f"/reviews/user/{user.id}/movie/{movie_id}/add", data={
        "title": "Emotional",
        "text": "Loved the tone",
        "user_rating": "9.0"
    }, follow_redirects=True)

    page = client.get(f"/reviews/user/{user.id}")
    soup = BeautifulSoup(page.data, "html.parser")
    review_row = next((r for r in soup.find_all("tr") if "Emotional" in r.text), None)
    review_id = review_row.find("form")["action"].split("/")[-1]

    response = client.post(f"/reviews/user/{user.id}/delete/{review_id}", follow_redirects=True)
    assert response.status_code == 200
    assert b"Emotional" not in response.data


@patch("blueprints.movies.fetch_movie")
def test_delete_review_invalid(mock_fetch, client, data_manager):
    """Should handle deletion of nonexistent review gracefully."""
    user = create_user_and_login(client, data_manager)

    response = client.post(
        f"/reviews/user/{user.id}/delete/999999",
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Review not found" in response.data or b"not found" in response.data.lower()
