"""
Pytest tests for review-related Flask routes, covering listing, detail,
adding, editing, and deleting reviews, with both valid flows and error cases.
"""
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup


# ---------------------- REVIEW TESTS ---------------------- #

@pytest.fixture
def create_review_user_and_movie(client, data_manager, register_user_and_login):
    """
    Create a new user, add a movie via mocked OMDb fetch, and return IDs.

    Returns:
        tuple: (user_id, movie_id) for use in review tests.
    """
    user = register_user_and_login(prefix="review")
    uid = data_manager.get_user_by_username(user['username']).id
    with patch("blueprints.movies.fetch_movie") as mock_fetch:
        mock_fetch.return_value = {"title": "Arrival", "year": "2016", "director": "Denis Villeneuve",
                                   "genre": "Sci-Fi", "poster_url": "", "imdb_rating": "8.0"}
        client.post(f"/movies/add/{uid}", data={"title": "Arrival", "year": "2016"}, follow_redirects=True)
    movie = data_manager.get_movies_by_user(uid)[0]
    return uid, movie.id


@pytest.mark.usefixtures("client", "data_manager")
class TestReviewListing:
    """
    Test listing of reviews by user and by movie.
    """

    @patch("blueprints.movies.fetch_movie")
    def test_user_reviews_page(self, mock_fetch, client, data_manager, create_review_user_and_movie):
        """
        Should display reviews for a given user.
        """
        uid, mid = create_review_user_and_movie
        client.post(f"/reviews/user/{uid}/movie/{mid}/add",
                    data={"title": "Stunning", "text": "Loved it!", "user_rating": "8.5"}, follow_redirects=True)
        response = client.get(f"/reviews/user/{uid}")
        assert response.status_code == 200
        assert b"stunning" in response.data.lower()

    @patch("blueprints.movies.fetch_movie")
    def test_movie_reviews_page(self, mock_fetch, client, data_manager, create_review_user_and_movie):
        """
        Should display reviews for a given movie.
        """
        uid, mid = create_review_user_and_movie
        client.post(f"/reviews/user/{uid}/movie/{mid}/add",
                    data={"title": "Twisty", "text": "Great plot!", "user_rating": "9.0"}, follow_redirects=True)
        response = client.get(f"/reviews/movie/{mid}")
        assert response.status_code == 200
        assert b"twisty" in response.data.lower()


@pytest.mark.usefixtures("client", "data_manager")
class TestReviewDetail:
    """
    Test review detail view for a specific review.
    """

    @patch("blueprints.movies.fetch_movie")
    def test_review_detail_page(self, mock_fetch, client, data_manager, create_review_user_and_movie):
        """
        Should show full review details, including text.
        """
        uid, mid = create_review_user_and_movie
        client.post(f"/reviews/user/{uid}/movie/{mid}/add",
                    data={"title": "Funny", "text": "Great humor", "user_rating": "8.5"}, follow_redirects=True)
        page = client.get(f"/reviews/user/{uid}")
        soup = BeautifulSoup(page.data, "html.parser")
        row = next(r for r in soup.find_all("tr") if "funny" in r.text.lower())
        rid = row.find("form")["action"].split("/")[-1]
        detail = client.get(f"/reviews/user/{uid}/review/{rid}")
        assert detail.status_code == 200
        assert b"great humor" in detail.data.lower()


@pytest.mark.usefixtures("client", "data_manager")
class TestReviewAdd:
    """
    Test adding new reviews with both valid and invalid data.
    """

    @patch("blueprints.movies.fetch_movie")
    def test_add_review_valid(self, mock_fetch, client, data_manager, create_review_user_and_movie):
        """
        Should add review and confirm addition when input is valid.
        """
        uid, mid = create_review_user_and_movie
        response = client.post(f"/reviews/user/{uid}/movie/{mid}/add",
                               data={"title": "Masterpiece", "text": "Beautiful visuals", "user_rating": "9.0"},
                               follow_redirects=True)
        assert response.status_code == 200
        assert b"review added" in response.data.lower()
        assert b"masterpiece" in response.data.lower()

    @patch("blueprints.movies.fetch_movie")
    def test_add_review_invalid(self, mock_fetch, client, data_manager, create_review_user_and_movie):
        """
        Should display errors when review input is invalid.
        """
        uid, mid = create_review_user_and_movie
        response = client.post(f"/reviews/user/{uid}/movie/{mid}/add",
                               data={"title": "", "text": "", "user_rating": "eleven"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"required" in response.data.lower() or b"invalid" in response.data.lower()


@pytest.mark.usefixtures("client", "data_manager")
class TestReviewEdit:
    """
    Test editing existing reviews for valid and invalid scenarios.
    """

    @pytest.fixture(autouse=True)
    def setup_review(self, client, data_manager, create_review_user_and_movie):
        """
        Create a review and store its ID for edit tests.
        """
        uid, mid = create_review_user_and_movie
        self.uid, self.mid = uid, mid
        client.post(f"/reviews/user/{uid}/movie/{mid}/add",
                    data={"title": "Solid", "text": "Cool", "user_rating": "7.5"}, follow_redirects=True)
        page = client.get(f"/reviews/user/{uid}")
        soup = BeautifulSoup(page.data, "html.parser")
        row = next(r for r in soup.find_all("tr") if "solid" in r.text.lower())
        self.rid = row.find("form")["action"].split("/")[-1]

    @patch("blueprints.movies.fetch_movie")
    def test_edit_review_valid(self, mock_fetch, client):
        """
        Should update review and reflect changes for valid data.
        """
        response = client.post(f"/reviews/user/{self.uid}/edit/{self.rid}",
                               data={"title": "Improved", "text": "Updated", "user_rating": "8.0"},
                               follow_redirects=True)
        assert response.status_code == 200
        assert b"improved" in response.data.lower()

    @patch("blueprints.movies.fetch_movie")
    def test_edit_review_invalid(self, mock_fetch, client):
        """
        Should display errors when edit input is invalid.
        """
        response = client.post(f"/reviews/user/{self.uid}/edit/{self.rid}",
                               data={"title": "", "text": "", "user_rating": "12.0"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"required" in response.data.lower() or b"rating must be" in response.data.lower()


@pytest.mark.usefixtures("client", "data_manager")
class TestReviewDelete:
    """
    Test deletion of reviews and error handling for invalid IDs.
    """

    @pytest.fixture(autouse=True)
    def setup_review(self, client, data_manager, create_review_user_and_movie):
        """
        Create a review and store its ID for delete tests.
        """
        uid, mid = create_review_user_and_movie
        self.uid, self.mid = uid, mid
        client.post(f"/reviews/user/{uid}/movie/{mid}/add",
                    data={"title": "Emotional", "text": "Loved", "user_rating": "9.0"}, follow_redirects=True)
        page = client.get(f"/reviews/user/{uid}")
        soup = BeautifulSoup(page.data, "html.parser")
        row = next(r for r in soup.find_all("tr") if "emotional" in r.text.lower())
        self.rid = row.find("form")["action"].split("/")[-1]

    def test_delete_review_valid(self, client):
        """
        Should delete the specified review and no longer list it.
        """
        response = client.post(f"/reviews/user/{self.uid}/delete/{self.rid}", follow_redirects=True)
        assert response.status_code == 200
        page = client.get(f"/reviews/user/{self.uid}")
        assert b"emotional" not in page.data.lower()

    def test_delete_review_invalid(self, client, data_manager, register_user_and_login):
        """
        Should display error when attempting to delete non-existent review.
        """
        user = register_user_and_login(prefix="reviewerr")
        uid = data_manager.get_user_by_username(user['username']).id
        response = client.post(f"/reviews/user/{uid}/delete/999999", follow_redirects=True)
        assert response.status_code == 200
        assert b"review not found" in response.data.lower()
