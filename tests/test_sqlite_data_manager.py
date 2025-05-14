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
    This fixture runs once per module.
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
    Create a fresh SQLiteDataManager instance per test.
    """
    db_url, _ = test_db
    return SQLiteDataManager(db_url)


@pytest.fixture
def session(test_db):
    """
    Provide a direct SQLAlchemy session for low-level DB access.
    """
    _, Session = test_db
    return Session()


# -------------------- Helper Functions -------------------- #

def create_user(dm: SQLiteDataManager, username="testuser") -> User:
    """
    Create and return a new user using the data manager.
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
    Should add a user and retrieve it from the database.
    """
    user = create_user(data_manager, "alice")
    users = data_manager.get_all_users()
    assert any(u.username == "alice" for u in users)


def test_update_user(data_manager):
    """
    Should update an existing user's field.
    """
    user = create_user(data_manager, "bob")
    updated = data_manager.update_user(user.id, {"first_name": "Bobby"})
    assert updated is not None
    assert updated.first_name == "Bobby"


def test_delete_user(data_manager):
    """
    Should delete a user and return True on success.
    """
    user = create_user(data_manager, "charlie")
    result = data_manager.delete_user(user.id)
    assert result is True

    # Ensure the user no longer exists
    assert data_manager.get_user_by_id(user.id) is None


def test_add_user_duplicate_username(data_manager):
    """
    Should not allow adding a user with an existing username.
    """
    user1 = create_user(data_manager, "diana")
    user2 = data_manager.add_user(
        username="diana",
        email="another@example.com",
        first_name="Dup",
        password_hash="hash"
    )
    assert user2 is None


def test_add_user_duplicate_email(data_manager):
    """
    Should not allow adding a user with an existing email.
    """
    user1 = create_user(data_manager, "edward")
    user2 = data_manager.add_user(
        username="edward2",
        email="edward@example.com",  # same email
        first_name="Dup",
        password_hash="hash"
    )
    assert user2 is None


def test_update_nonexistent_user(data_manager):
    """
    Should return None when trying to update a non-existent user.
    """
    result = data_manager.update_user(99999, {"first_name": "Ghost"})
    assert result is None


def test_delete_nonexistent_user(data_manager):
    """
    Should return False when trying to delete a non-existent user.
    """
    result = data_manager.delete_user(99999)
    assert result is False


# -------------------- Movie Tests -------------------- #

def test_add_movie_and_get_by_user(data_manager):
    """
    Should add a movie and link it to the user.
    """
    user = create_user(data_manager, "fiona")
    movie = create_movie(data_manager, user.id, "Inception")
    movies = data_manager.get_movies_by_user(user.id)
    assert any(m.title == "Inception" for m in movies)


def test_get_all_movies(data_manager):
    """
    Should return all movies in the database.
    """
    user = create_user(data_manager, "greg")
    create_movie(data_manager, user.id, "Matrix")
    create_movie(data_manager, user.id, "Interstellar")
    movies = data_manager.get_all_movies()
    titles = [m.title for m in movies]
    assert "Matrix" in titles
    assert "Interstellar" in titles


def test_update_movie(data_manager):
    """
    Should update movie details.
    """
    user = create_user(data_manager, "hannah")
    movie = create_movie(data_manager, user.id, "Old Title")
    updated = data_manager.update_movie(movie.id, {"title": "New Title"})
    assert updated.title == "New Title"


def test_delete_movie(data_manager):
    """
    Should delete a movie and return True on success.
    """
    user = create_user(data_manager, "ian")
    movie = create_movie(data_manager, user.id, "To Delete")
    result = data_manager.delete_movie(movie.id)
    assert result is True

    # Ensure the movie no longer exists
    assert data_manager.get_movie_by_id(movie.id) is None


def test_add_movie_for_nonexistent_user(data_manager):
    """
    Should return None when trying to add a movie for a non-existent user.
    """
    movie_data = {
        "title": "Ghost Film",
        "year": 1999
    }
    result = data_manager.add_movie(user_id=99999, movie_data=movie_data)
    assert result is None


def test_add_duplicate_movie_links_only_once(data_manager, session):
    """
    Should only link a user to a movie once, and merge the status flags.
    """
    user = create_user(data_manager, "julia")
    movie_data = {
        "title": "Blade Runner",
        "year": 1982
    }

    # Add once with is_planned=True
    data_manager.add_movie(user.id, movie_data, planned=True)

    # Add again with is_watched=True, should update the link
    data_manager.add_movie(user.id, movie_data, watched=True)

    with session as s:
        link = s.query(UserMovie).filter_by(user_id=user.id).first()
        assert link is not None
        assert link.is_planned is True
        assert link.is_watched is True


# -------------------- Review Tests -------------------- #

def test_add_and_get_review_by_user(data_manager):
    """
    Should add a review and retrieve it via user ID.
    """
    user = create_user(data_manager, "karl")
    movie = create_movie(data_manager, user.id)
    review = create_review(data_manager, user.id, movie.id)

    reviews = data_manager.get_reviews_by_user(user.id)
    assert any(r.title == "My Review" for r in reviews)
    assert any(r.movie.title == movie.title for r in reviews)


def test_get_reviews_for_movie(data_manager):
    """
    Should return all reviews for a given movie.
    """
    user = create_user(data_manager, "laura")
    movie = create_movie(data_manager, user.id)
    create_review(data_manager, user.id, movie.id)

    reviews = data_manager.get_reviews_for_movie(movie.id)
    assert any(r.text == "Great movie!" for r in reviews)
    assert all(r.movie_id == movie.id for r in reviews)


def test_get_review_detail(data_manager):
    """
    Should retrieve full review with user and movie relations.
    """
    user = create_user(data_manager, "mike")
    movie = create_movie(data_manager, user.id)
    review = create_review(data_manager, user.id, movie.id)

    detailed_review = data_manager.get_review_detail(review.id)
    assert detailed_review is not None
    assert detailed_review.user.username == "mike"
    assert detailed_review.movie.title == movie.title


def test_update_review(data_manager):
    """
    Should update an existing review's text field.
    """
    user = create_user(data_manager, "nina")
    movie = create_movie(data_manager, user.id)
    review = create_review(data_manager, user.id, movie.id)

    updated = data_manager.update_review(review.id, {"text": "Updated review text"})
    assert updated.text == "Updated review text"


def test_delete_review(data_manager):
    """
    Should delete a review and return True on success.
    """
    user = create_user(data_manager, "oliver")
    movie = create_movie(data_manager, user.id)
    review = create_review(data_manager, user.id, movie.id)

    result = data_manager.delete_review(review.id)
    assert result is True
    assert data_manager.get_review_by_id(review.id) is None


def test_add_review_with_invalid_user_or_movie(data_manager):
    """
    Should return None if user or movie does not exist.
    """
    result1 = data_manager.add_review(
        user_id=9999,
        movie_id=1,
        review_data={"title": "Fail", "user_rating": 5}
    )
    result2 = data_manager.add_review(
        user_id=1,
        movie_id=9999,
        review_data={"title": "Fail", "user_rating": 5}
    )
    assert result1 is None
    assert result2 is None


def test_update_nonexistent_review(data_manager):
    """
    Should return None when updating a non-existent review.
    """
    result = data_manager.update_review(9999, {"text": "Should not work"})
    assert result is None


def test_delete_nonexistent_review(data_manager):
    """
    Should return False when deleting a non-existent review.
    """
    result = data_manager.delete_review(9999)
    assert result is False
