import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from datamanager.models import Base, User, Movie, Review
from datamanager.sqlite_data_manager import SQLiteDataManager

# Setup test database
temp_db = tempfile.NamedTemporaryFile(delete=False)
TEST_DB_URL = f"sqlite:///{temp_db.name}"
engine = create_engine(TEST_DB_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

data_manager = SQLiteDataManager(TEST_DB_URL)


def setup_user(name="TestUser"):
    with Session() as session:
        user = User(name=name)
        session.add(user)
        session.commit()
        return session.get(User, user.id)


def setup_movie(user_id, title="Test Movie"):
    with Session() as session:
        movie = Movie(title=title, user_id=user_id)
        session.add(movie)
        session.commit()
        return session.get(Movie, movie.id)


def setup_review(user_id, movie_id, text="Test Review", rating=7.0):
    with Session() as session:
        review = Review(user_id=user_id, movie_id=movie_id, text=text, user_rating=rating)
        session.add(review)
        session.commit()
        return session.get(Review, review.id)


def test_add_user_and_get_all_users():
    data_manager.add_user("Alice")
    users = data_manager.get_all_users()
    assert any(u.name == "Alice" for u in users)


def test_update_user():
    user = data_manager.add_user("Bob")
    updated = data_manager.update_user(user.id, "Bobby")
    assert updated.name == "Bobby"


def test_delete_user():
    user = data_manager.add_user("Charlie")
    result = data_manager.delete_user(user.id)
    assert result is True


def test_add_movie_and_get_user_movies():
    user = setup_user()
    movie_data = {"title": "Inception", "director": "Nolan", "year": "2010", "rating": 8.8}
    data_manager.add_movie(user.id, movie_data)
    movies = data_manager.get_user_movies(user.id)
    assert any(m.title == "Inception" for m in movies)


def test_update_movie():
    user = setup_user()
    movie = setup_movie(user.id, "Old Title")
    updated = data_manager.update_movie(movie.id, {"title": "New Title"})
    assert updated.title == "New Title"


def test_delete_movie():
    user = setup_user()
    movie = setup_movie(user.id, "To Delete")
    result = data_manager.delete_movie(movie.id)
    assert result is True


def test_add_and_get_review_by_user():
    user = setup_user()
    movie = setup_movie(user.id)
    review_data = {"text": "Great!", "user_rating": 9.0}
    data_manager.add_review(user.id, movie.id, review_data)
    reviews = data_manager.get_reviews_by_user(user.id)
    assert any(r.text == "Great!" for r in reviews)


def test_get_reviews_for_movie():
    user = setup_user()
    movie = setup_movie(user.id)
    setup_review(user.id, movie.id, "Interesting", 7.5)
    reviews = data_manager.get_reviews_for_movie(movie.id)
    assert any(r.text == "Interesting" for r in reviews)


def test_update_review():
    user = setup_user()
    movie = setup_movie(user.id)
    review = setup_review(user.id, movie.id)
    updated = data_manager.update_review(review.id, {"text": "Updated Text"})
    assert updated.text == "Updated Text"


def test_delete_review():
    user = setup_user()
    movie = setup_movie(user.id)
    review = setup_review(user.id, movie.id)
    result = data_manager.delete_review(review.id)
    assert result is True
