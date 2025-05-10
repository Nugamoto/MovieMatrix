import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_page(client):
    pass


def test_users_page(client):
    pass


def test_add_user_valid(client):
    pass


def test_add_user_invalid(client):
    pass


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
