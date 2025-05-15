import uuid
from unittest.mock import patch

from bs4 import BeautifulSoup
from werkzeug.security import generate_password_hash


# ---------------------- Helpers -------------------------- #

def create_user_and_login(client, data_manager):
    """Create a user and log them in for test purposes."""
    unique = uuid.uuid4().hex[:6]
    username = f"user_{unique}"
    email = f"{username}@test.com"
    password = "secret123"
    user = data_manager.add_user(username, email, "Movie", password_hash=generate_password_hash(password))
    client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
    return user


# ---------------------- Movie Tests -------------------------- #

def test_movies_page(client):
    """Should render the global movie list."""
    response = client.get("/movies", follow_redirects=True)
    assert response.status_code == 200
    assert b"Movies" in response.data


@patch("blueprints.movies.fetch_movie")
def test_add_movie_valid(mock_fetch, client, data_manager):
    """Should allow adding a valid movie using OMDb lookup."""
    user = create_user_and_login(client, data_manager)

    mock_fetch.return_value = {
        "title": "Inception",
        "year": "2010",
        "director": "Christopher Nolan",
        "genre": "Sci-Fi",
        "poster_url": "",
        "imdb_rating": "8.8",
    }

    response = client.post(
        f"/movies/add/{user.id}",
        data={"title": "Inception", "year": "2010"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"added" in response.data or b"Movie" in response.data


@patch("blueprints.movies.fetch_movie")
def test_add_movie_invalid(mock_fetch, client, data_manager):
    """Should show a warning when OMDb lookup fails (invalid title)."""
    user = create_user_and_login(client, data_manager)

    mock_fetch.return_value = None  # Simulate OMDb failure

    response = client.post(
        f"/movies/add/{user.id}",
        data={"title": "SomeFakeTitleThatDoesNotExist_9999"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"No movie found" in response.data or b"not found" in response.data.lower()


@patch("blueprints.movies.fetch_movie")
def test_user_movies_page(mock_fetch, client, data_manager):
    """Should display a user's movie list after adding a movie."""
    user = create_user_and_login(client, data_manager)

    mock_fetch.return_value = {
        "title": "Interstellar",
        "year": "2014",
        "director": "Christopher Nolan",
        "genre": "Sci-Fi",
        "poster_url": "",
        "imdb_rating": "8.6",
    }

    client.post(
        f"/movies/add/{user.id}",
        data={"title": "Interstellar", "year": "2014"},
        follow_redirects=True
    )

    response = client.get(f"/users/{user.id}", follow_redirects=True)
    assert response.status_code == 200
    assert b"Interstellar" in response.data or b"Movies" in response.data


@patch("blueprints.movies.fetch_movie")
def test_update_movie_valid(mock_fetch, client, data_manager):
    """Should allow updating a movie's metadata."""
    user = create_user_and_login(client, data_manager)

    mock_fetch.return_value = {
        "title": "Blade Runner",
        "year": "1982",
        "director": "Ridley Scott",
        "genre": "Sci-Fi",
        "poster_url": "",
        "imdb_rating": "8.1",
    }

    client.post(
        f"/movies/add/{user.id}",
        data={"title": "Blade Runner", "year": "1982"},
        follow_redirects=True,
    )

    page = client.get(f"/users/{user.id}", follow_redirects=True)
    soup = BeautifulSoup(page.data, "html.parser")
    update_links = [
        a for a in soup.find_all("a", href=True)
        if f"/movies/edit/{user.id}/" in a["href"]
    ]
    assert update_links, "No update link found"
    movie_id = update_links[0]["href"].split("/")[-1]

    response = client.post(
        f"/movies/edit/{user.id}/{movie_id}",
        data={
            "title": "Blade Runner Final",
            "director": "Ridley Scott",
            "year": "1982",
            "genre": "Neo-Noir",
            "imdb_rating": "8.5",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Movie updated." in response.data
    assert b"Blade Runner Final" in response.data


@patch("blueprints.movies.fetch_movie")
def test_update_movie_invalid_data(mock_fetch, client, data_manager):
    """Should reject invalid metadata (e.g. bad year, bad rating)."""
    user = create_user_and_login(client, data_manager)

    mock_fetch.return_value = {
        "title": "Dune",
        "year": "2021",
        "director": "Denis Villeneuve",
        "genre": "Sci-Fi",
        "poster_url": "",
        "imdb_rating": "8.2",
    }

    client.post(
        f"/movies/add/{user.id}",
        data={"title": "Dune", "year": "2021"},
        follow_redirects=True
    )

    page = client.get(f"/users/{user.id}", follow_redirects=True)
    soup = BeautifulSoup(page.data, "html.parser")
    update_links = [
        a for a in soup.find_all("a", href=True)
        if f"/movies/edit/{user.id}/" in a["href"]
    ]
    assert update_links, "No update link found"
    movie_id = update_links[0]["href"].split("/")[-1]

    # Invalid year & rating
    response = client.post(
        f"/movies/edit/{user.id}/{movie_id}",
        data={"title": "Dune", "year": "NaN", "imdb_rating": "99"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid year" in response.data or b"IMDb rating must be" in response.data


@patch("blueprints.movies.fetch_movie")
def test_delete_movie_valid(mock_fetch, client, data_manager):
    """Should successfully delete a movie and show a success message."""
    user = create_user_and_login(client, data_manager)

    mock_fetch.return_value = {
        "title": "Tenet",
        "year": "2020",
        "director": "Christopher Nolan",
        "genre": "Sci-Fi",
        "poster_url": "",
        "imdb_rating": "7.4",
    }

    client.post(
        f"/movies/add/{user.id}",
        data={"title": "Tenet", "year": "2020"},
        follow_redirects=True,
    )

    page = client.get(f"/users/{user.id}", follow_redirects=True)
    soup = BeautifulSoup(page.data, "html.parser")

    delete_form = next(
        (f for f in soup.find_all("form", action=True)
         if f"/movies/delete/{user.id}/" in f["action"]),
        None
    )
    assert delete_form is not None, "No delete form found"
    movie_id = delete_form["action"].split("/")[-1]

    response = client.post(
        f"/movies/delete/{user.id}/{movie_id}",
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Movie deleted" in response.data or b"deleted" in response.data


def test_delete_movie_invalid(client, data_manager):
    """Should show a warning when trying to delete a non-existent movie."""
    user = create_user_and_login(client, data_manager)

    response = client.post(
        f"/movies/delete/{user.id}/999999",
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Movie not found" in response.data or b"not found" in response.data.lower()
