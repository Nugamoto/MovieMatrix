import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from datamanager.models import Base, User, Movie, Review, UserMovie
from datamanager.sqlite_data_manager import SQLiteDataManager


# -------------------- Test Setup -------------------- #

@pytest.fixture(scope="module")
def test_db():
    """
    Create a temporary SQLite database for testing.

    This fixture initializes a SQLite database in a temporary file,
    creates all tables, and returns the database URL and session factory.
    Runs once per module.
    """
    temp_db = tempfile.NamedTemporaryFile(delete=False)
    db_url = f"sqlite:///{temp_db.name}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    yield db_url, Session
    engine.dispose()


@pytest.fixture
def data_manager(test_db):
    """
    Provide a fresh SQLiteDataManager instance per test.
    """
    db_url, _ = test_db
    return SQLiteDataManager(db_url)


@pytest.fixture
def session(test_db):
    """
    Provide a direct SQLAlchemy session for low-level database access.
    """
    _, Session = test_db
    return Session()


# -------------------- Helper Functions -------------------- #

def create_user(dm: SQLiteDataManager, username="testuser") -> User:
    """
    Create and return a new user via the data manager.

    Args:
        dm: The SQLiteDataManager instance.
        username: Desired username.

    Returns:
        The created User object.
    """
    return dm.add_user(
        username=username,
        email=f"{username}@example.com",
        first_name="Test",
        last_name="User",
        age=30,
        password_hash="testhash"
    )


def create_movie(dm: SQLiteDataManager, user_id: int, title="Test Movie") -> Movie:
    """
    Create and link a movie to a user.

    Args:
        dm: The SQLiteDataManager instance.
        user_id: ID of the user to link to.
        title: Title of the movie.

    Returns:
        The created Movie object.
    """
    movie_data = {
        "title": title,
        "director": "Some Director",
        "year": 2020,
        "genre": "Drama",
        "poster_url": "http://example.com/poster.jpg",
        "imdb_rating": 7.5
    }
    return dm.add_movie(user_id=user_id, movie_data=movie_data)


def create_review(dm: SQLiteDataManager, user_id: int, movie_id: int) -> Review:
    """
    Create and return a review for the given user and movie.

    Args:
        dm: The SQLiteDataManager instance.
        user_id: ID of the user making the review.
        movie_id: ID of the movie being reviewed.

    Returns:
        The created Review object.
    """
    return dm.add_review(
        user_id=user_id,
        movie_id=movie_id,
        review_data={
            "title": "My Review",
            "text": "Great movie!",
            "user_rating": 8.5
        }
    )


# -------------------- User Tests -------------------- #

def test_add_user_and_get_all_users(data_manager):
    """
    Add a user and verify it appears in get_all_users().
    """
    user = create_user(data_manager, "alice")
    users = data_manager.get_all_users()
    assert any(u.username == "alice" for u in users)


def test_update_user(data_manager):
    """
    Update an existing user's field and verify it persists.
    """
    user = create_user(data_manager, "bob")
    updated = data_manager.update_user(user.id, {"first_name": "Bobby"})
    assert updated is not None
    assert updated.first_name == "Bobby"


def test_delete_user(data_manager):
    """
    Delete a user and ensure removal.
    """
    user = create_user(data_manager, "charlie")
    result = data_manager.delete_user(user.id)
    assert result is True
    assert data_manager.get_user_by_id(user.id) is None


def test_add_user_duplicate_username(data_manager):
    """
    Prevent adding users with duplicate usernames.
    """
    create_user(data_manager, "diana")
    duplicate = data_manager.add_user(
        username="diana",
        email="another@example.com",
        first_name="Dup",
        password_hash="hash"
    )
    assert duplicate is None


def test_add_user_duplicate_email(data_manager):
    """
    Prevent adding users with duplicate emails.
    """
    create_user(data_manager, "edward")
    duplicate = data_manager.add_user(
        username="edward2",
        email="edward@example.com",
        first_name="Dup",
        password_hash="hash"
    )
    assert duplicate is None


def test_update_nonexistent_user(data_manager):
    """
    Return None when updating a non-existent user.
    """
    result = data_manager.update_user(99999, {"first_name": "Ghost"})
    assert result is None


def test_delete_nonexistent_user(data_manager):
    """
    Return False when deleting a non-existent user.
    """
    result = data_manager.delete_user(99999)
    assert result is False


# -------------------- Movie Tests -------------------- #

def test_add_movie_and_get_by_user(data_manager):
    """
    Add a movie and verify it's linked to the user.
    """
    user = create_user(data_manager, "fiona")
    movie = create_movie(data_manager, user.id, "Inception")
    movies = data_manager.get_movies_by_user(user.id)
    assert any(m.title == "Inception" for m in movies)


def test_get_all_movies(data_manager):
    """
    Retrieve all movies in the database.
    """
    user = create_user(data_manager, "greg")
    create_movie(data_manager, user.id, "Matrix")
    create_movie(data_manager, user.id, "Interstellar")
    movies = data_manager.get_all_movies()
    titles = [m.title for m in movies]
    assert "Matrix" in titles and "Interstellar" in titles


def test_update_movie(data_manager):
    """
    Update movie details and verify change.
    """
    user = create_user(data_manager, "hannah")
    movie = create_movie(data_manager, user.id, "Old Title")
    updated = data_manager.update_movie(movie.id, {"title": "New Title"})
    assert updated.title == "New Title"


def test_delete_movie(data_manager):
    """
    Delete a movie and ensure removal.
    """
    user = create_user(data_manager, "ian")
    movie = create_movie(data_manager, user.id, "To Delete")
    result = data_manager.delete_movie(movie.id)
    assert result is True
    assert data_manager.get_movie_by_id(movie.id) is None


def test_add_movie_for_nonexistent_user(data_manager):
    """
    Return None when adding a movie for a non-existent user.
    """
    result = data_manager.add_movie(user_id=99999, movie_data={"title": "Ghost Film", "year": 1999})
    assert result is None


def test_add_duplicate_movie_links_only_once(data_manager, session):
    """
    Link a user to a movie only once, merging status flags.
    """
    user = create_user(data_manager, "julia")
    data_manager.add_movie(user.id, {"title": "Blade Runner", "year": 1982}, planned=True)
    data_manager.add_movie(user.id, {"title": "Blade Runner", "year": 1982}, watched=True)
    with session as s:
        link = s.query(UserMovie).filter_by(user_id=user.id).first()
        assert link and link.is_planned and link.is_watched


# -------------------- Review Tests -------------------- #

def test_add_and_get_review_by_user(data_manager):
    """
    Add a review and retrieve via user ID.
    """
    user = create_user(data_manager, "karl")
    movie = create_movie(data_manager, user.id)
    review = create_review(data_manager, user.id, movie.id)
    reviews = data_manager.get_reviews_by_user(user.id)
    assert any(r.title == "My Review" for r in reviews)
    assert any(r.movie.title == movie.title for r in reviews)


def test_get_reviews_for_movie(data_manager):
    """
    Retrieve all reviews for a specific movie.
    """
    user = create_user(data_manager, "laura")
    movie = create_movie(data_manager, user.id)
    create_review(data_manager, user.id, movie.id)
    reviews = data_manager.get_reviews_for_movie(movie.id)
    assert any(r.text == "Great movie!" for r in reviews)
    assert all(r.movie_id == movie.id for r in reviews)


def test_get_review_detail(data_manager):
    """
    Retrieve full review with user and movie relations.
    """
    user = create_user(data_manager, "mike")
    movie = create_movie(data_manager, user.id)
    review = create_review(data_manager, user.id, movie.id)
    detail = data_manager.get_review_detail(review.id)
    assert detail and detail.user.username == "mike" and detail.movie.title == movie.title


def test_update_review(data_manager):
    """
    Update an existing review's text and verify.
    """
    user = create_user(data_manager, "nina")
    movie = create_movie(data_manager, user.id)
    review = create_review(data_manager, user.id, movie.id)
    updated = data_manager.update_review(review.id, {"text": "Updated review text"})
    assert updated.text == "Updated review text"


def test_delete_review(data_manager):
    """
    Delete a review and ensure removal.
    """
    user = create_user(data_manager, "oliver")
    movie = create_movie(data_manager, user.id)
    review = create_review(data_manager, user.id, movie.id)
    result = data_manager.delete_review(review.id)
    assert result is True
    assert data_manager.get_review_by_id(review.id) is None


def test_add_review_with_invalid_user_or_movie(data_manager):
    """
    Return None if user or movie does not exist when adding review.
    """
    assert data_manager.add_review(user_id=9999, movie_id=1, review_data={"title": "Fail", "user_rating": 5}) is None
    assert data_manager.add_review(user_id=1, movie_id=9999, review_data={"title": "Fail", "user_rating": 5}) is None


def test_update_nonexistent_review(data_manager):
    """
    Return None when updating a non-existent review.
    """
    assert data_manager.update_review(9999, {"text": "Does not exist"}) is None


def test_delete_nonexistent_review(data_manager):
    """
    Return False when deleting a non-existent review.
    """
    assert data_manager.delete_review(9999) is False


# -------------------- Statistics Tests -------------------- #

def test_count_users(data_manager):
    """
    Return correct number of users.
    """
    create_user(data_manager, "user1")
    create_user(data_manager, "user2")
    assert data_manager.count_users() >= 2


def test_count_movies(data_manager):
    """
    Return correct number of movies.
    """
    user = create_user(data_manager, "movietester")
    create_movie(data_manager, user.id, "Movie A")
    create_movie(data_manager, user.id, "Movie B")
    assert data_manager.count_movies() >= 2


def test_count_reviews(data_manager):
    """
    Return correct number of reviews.
    """
    user = create_user(data_manager, "reviewer")
    movie = create_movie(data_manager, user.id, "Reviewed Movie")
    create_review(data_manager, user.id, movie.id)
    assert data_manager.count_reviews() >= 1
