"""
Pytest tests for movie-related Flask routes, including listing, adding,
updating, deleting, and form retrieval, covering valid flows, input errors,
authorization, and edge cases.
"""
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from werkzeug.security import generate_password_hash


# ---------------------- MOVIE TESTS ---------------------- #

@pytest.mark.usefixtures("client", "data_manager", "register_user_and_login")
class TestMovieList:
    """
    Test listing of movies page for authenticated users.
    """

    def test_movies_page(self, client):
        """
        Should return 200 and display movies list header.
        """
        response = client.get("/movies", follow_redirects=True)
        assert response.status_code == 200
        assert b"movies" in response.data.lower()


@pytest.mark.usefixtures("client", "data_manager", "register_user_and_login")
class TestMovieAdd:
    """
    Test adding movies via POST with valid data using mocked OMDb fetch.
    """

    @patch("blueprints.movies.fetch_movie")
    def test_add_movie_valid(self, mock_fetch, client, data_manager, register_user_and_login):
        """
        Should add movie to user's list when OMDb returns valid data.
        """
        user = register_user_and_login(prefix="movie")
        uid = data_manager.get_user_by_username(user['username']).id
        mock_fetch.return_value = {
            "title": "Inception", "year": "2010",
            "director": "Christopher Nolan", "genre": "Sci-Fi",
            "poster_url": "", "imdb_rating": "8.8"
        }
        response = client.post(f"/movies/add/{uid}", data={"title": "Inception", "year": "2010"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"added" in response.data.lower()


@pytest.mark.usefixtures("client", "data_manager", "register_user_and_login")
class TestMovieAddErrors:
    """
    Test error handling when adding movies with invalid input or unauthorized access.
    """

    def test_add_movie_unauthorized(self, client, register_user_and_login):
        """
        Should redirect to login when adding to another user's list.
        """
        u1 = register_user_and_login(prefix="u1")
        dm = client.application.data_manager
        u2 = dm.add_user("u2", "u2@test.com", "Movie", password_hash=generate_password_hash("secret123"))
        response = client.get(f"/movies/add/{u2.id}", follow_redirects=True)
        assert response.status_code == 200
        assert b"login" in response.data.lower()

    @patch("blueprints.movies.fetch_movie")
    def test_add_movie_missing_title(self, mock_fetch, client, data_manager, register_user_and_login):
        """
        Should show error when title field is empty.
        """
        user = register_user_and_login(prefix="movie")
        uid = data_manager.get_user_by_username(user['username']).id
        response = client.post(f"/movies/add/{uid}", data={"title": "", "year": "2010"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"movie title is required" in response.data.lower()

    @patch("blueprints.movies.fetch_movie")
    def test_add_movie_invalid_year(self, mock_fetch, client, data_manager, register_user_and_login):
        """
        Should display error for non-numeric year input.
        """
        user = register_user_and_login(prefix="movie")
        uid = data_manager.get_user_by_username(user['username']).id
        response = client.post(f"/movies/add/{uid}", data={"title": "Test", "year": "20ab"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"invalid year format" in response.data.lower()

    def test_add_movie_user_not_found(self, client, register_user_and_login):
        """
        Should handle adding movie for non-existent user.
        """
        register_user_and_login(prefix="movie")
        response = client.post("/movies/add/99999", data={"title": "Test", "year": "2000"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"users" in response.data.lower()


@pytest.mark.usefixtures("client", "data_manager", "register_user_and_login")
class TestMovieUpdateValid:
    """
    Test successful update of existing movie entries.
    """

    @pytest.fixture(autouse=True)
    def setup_movie(self, client, data_manager, register_user_and_login):
        """
        Create and retrieve movie ID for update tests.
        """
        user = register_user_and_login(prefix="movie")
        self.uid = data_manager.get_user_by_username(user['username']).id
        with patch("blueprints.movies.fetch_movie") as mock_fetch:
            mock_fetch.return_value = {"title": "Orig", "year": "2000", "director": "D", "genre": "G", "poster_url": "",
                                       "imdb_rating": "7.0"}
            client.post(f"/movies/add/{self.uid}", data={"title": "Orig", "year": "2000"}, follow_redirects=True)
        page = client.get(f"/users/{self.uid}", follow_redirects=True)
        soup = BeautifulSoup(page.data, "html.parser")
        link = next(a for a in soup.find_all("a", href=True) if f"/movies/edit/{self.uid}/" in a["href"])
        self.mid = link["href"].split("/")[-1]

    @patch("blueprints.movies.fetch_movie")
    def test_update_movie_valid(self, mock_fetch, client):
        """
        Should update movie details and show confirmation.
        """
        mock_fetch.return_value = None
        response = client.post(f"/movies/edit/{self.uid}/{self.mid}",
                               data={"title": "New", "director": "D", "year": "2000", "genre": "NG",
                                     "imdb_rating": "8.5"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"movie updated" in response.data.lower()
        assert b"new" in response.data.lower()


@pytest.mark.usefixtures("client", "data_manager", "register_user_and_login")
class TestMovieUpdateErrors:
    """
    Test error handling during movie update for unauthorized or invalid cases.
    """

    def test_update_movie_unauthorized(self, client, register_user_and_login):
        """
        Should require login when updating another user's movie.
        """
        u1 = register_user_and_login(prefix="u1")
        dm = client.application.data_manager
        movie = dm.add_movie(dm.get_user_by_username(u1['username']).id, {"title": "T", "year": "2000"}, False, False,
                             False)
        register_user_and_login(prefix="u2")
        response = client.post(f"/movies/edit/{dm.get_user_by_username(u1['username']).id}/{movie.id}",
                               follow_redirects=True)
        assert response.status_code == 200
        assert b"login" in response.data.lower()

    def test_update_movie_not_found(self, client, register_user_and_login, data_manager):
        """
        Should handle non-existent movie or user gracefully.
        """
        u = register_user_and_login(prefix="movie")
        uid = data_manager.get_user_by_username(u['username']).id
        response = client.post(f"/movies/edit/{uid}/99999", follow_redirects=True)
        assert response.status_code == 200
        assert b"user or movie not found" in response.data.lower()

    @patch("blueprints.movies.fetch_movie")
    def test_update_movie_invalid_rating(self, mock_fetch, client, data_manager, register_user_and_login):
        """
        Should validate imdb_rating is within 0-10.
        """
        u = register_user_and_login(prefix="movie")
        uid = data_manager.get_user_by_username(u['username']).id
        movie = data_manager.add_movie(uid, {"title": "X", "year": "2000"}, False, False, False)
        response = client.post(f"/movies/edit/{uid}/{movie.id}",
                               data={"title": "X", "year": "2000", "imdb_rating": "11"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"imdb rating must be 0-10" in response.data.lower()


@pytest.mark.usefixtures("client", "data_manager", "register_user_and_login")
class TestMovieDeleteValid:
    """
    Test successful deletion of a user's movie.
    """

    @pytest.fixture(autouse=True)
    def setup_movie(self, client, data_manager, register_user_and_login):
        """
        Create and retrieve movie ID for delete tests.
        """
        u = register_user_and_login(prefix="movie")
        self.uid = data_manager.get_user_by_username(u['username']).id
        with patch("blueprints.movies.fetch_movie") as mock_fetch:
            mock_fetch.return_value = {"title": "Del", "year": "2001", "director": "D", "genre": "G", "poster_url": "",
                                       "imdb_rating": "7.1"}
            client.post(f"/movies/add/{self.uid}", data={"title": "Del", "year": "2001"}, follow_redirects=True)
        page = client.get(f"/users/{self.uid}", follow_redirects=True)
        soup = BeautifulSoup(page.data, "html.parser")
        form = next(f for f in soup.find_all("form", action=True) if f"/movies/delete/{self.uid}/" in f["action"])
        self.mid = form["action"].split("/")[-1]

    def test_delete_movie_valid(self, client):
        """
        Should delete specified movie and confirm deletion.
        """
        response = client.post(f"/movies/delete/{self.uid}/{self.mid}", follow_redirects=True)
        assert response.status_code == 200
        assert b"movie deleted" in response.data.lower()


@pytest.mark.usefixtures("client", "data_manager", "register_user_and_login")
class TestMovieDeleteErrors:
    """
    Test unauthorized deletion attempt of another user's movie.
    """

    def test_delete_movie_unauthorized(self, client, register_user_and_login):
        """
        Should require login when deleting another user's movie.
        """
        u1 = register_user_and_login(prefix="u1")
        dm = client.application.data_manager
        movie = dm.add_movie(dm.get_user_by_username(u1['username']).id, {"title": "D", "year": "2000"}, False, False,
                             False)
        register_user_and_login(prefix="u2")
        response = client.post(f"/movies/delete/{dm.get_user_by_username(u1['username']).id}/{movie.id}",
                               follow_redirects=True)
        assert response.status_code == 200
        assert b"login" in response.data.lower()


@pytest.mark.usefixtures("client", "data_manager", "register_user_and_login")
class TestMovieGETForms:
    """
    Test GET requests for movie add and edit forms retrieval.
    """

    def test_add_movie_get_form(self, client, data_manager, register_user_and_login):
        """
        Should display add movie form.
        """
        u = register_user_and_login(prefix="movie")
        uid = data_manager.get_user_by_username(u['username']).id
        response = client.get(f"/movies/add/{uid}", follow_redirects=True)
        assert response.status_code == 200
        assert b"add movie" in response.data.lower()

    def test_update_movie_get_form(self, client, data_manager, register_user_and_login):
        """
        Should display edit movie form with existing data.
        """
        u = register_user_and_login(prefix="movie")
        uid = data_manager.get_user_by_username(u['username']).id
        with patch("blueprints.movies.fetch_movie") as mock_fetch:
            mock_fetch.return_value = {"title": "Form", "year": "2002", "director": "D", "genre": "G", "poster_url": "",
                                       "imdb_rating": "7.2"}
            client.post(f"/movies/add/{uid}", data={"title": "Form", "year": "2002"}, follow_redirects=True)
        page = client.get(f"/users/{uid}", follow_redirects=True)
        soup = BeautifulSoup(page.data, "html.parser")
        link = next(a for a in soup.find_all("a", href=True) if f"/movies/edit/{uid}/" in a["href"])
        mid = link["href"].split("/")[-1]
        response = client.get(f"/movies/edit/{uid}/{mid}", follow_redirects=True)
        assert response.status_code == 200
        assert b"edit movie" in response.data.lower()
