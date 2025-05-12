import logging

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, joinedload
from werkzeug.security import generate_password_hash

from datamanager.data_manager_interface import DataManagerInterface
from datamanager.models import User, Movie, Review, UserMovie

logger = logging.getLogger(__name__)


class SQLiteDataManager(DataManagerInterface):
    """
    Concrete implementation of DataManagerInterface using SQLite + SQLAlchemy.

    Provides CRUD operations for users, movies, reviews and the user_movies link
    table.  Each method opens a short-lived session via context manager to keep
    transactions explicit and connections short-lived.
    """

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    def get_all_users(self):
        """Return all users from the database.

        Returns:
            list[User]: A list of all users.
        """
        with self.Session() as session:
            result = session.execute(select(User))
            return result.scalars().all()

    def get_all_movies(self):
        """Return all movies stored in the database.

        This method retrieves all movie records available across all users.
        It is used when movie data must be accessed independently of the user
        (e.g., for public listings or cross-user aggregations).

        Returns:
            list[Movie]: A list of all Movie objects stored in the database.
        """
        with self.Session() as session:
            result = session.execute(select(Movie))
            return result.scalars().all()

    def get_movies_by_user(self, user_id: int):
        """
        Return all movies that are linked to a user via the user_movies table.

        Args:
            user_id (int): ID of the user.

        Returns:
            list[Movie]: All movies associated with the user.
        """
        with self.Session() as session:
            stmt = (
                select(Movie)
                .join(UserMovie, Movie.id == UserMovie.movie_id)
                .where(UserMovie.user_id == user_id)
            )
            return session.execute(stmt).scalars().all()

    def add_user(
            self,
            username: str,
            email: str,
            first_name: str,
            password_hash: str | None = None,
            last_name: str | None = None,
            age: int | None = None,
    ) -> User | None:
        """
        Create a user with all mandatory fields.

        Args:
            username (str): Unique username.
            email (str): Unique e-mail address.
            first_name (str): First name (required).
            password_hash (str | None): Already-hashed password; if None,
                                        a hash for 'changeme' is generated.
            last_name (str | None): Optional last name.
            age (int | None): Optional age.

        Returns:
            User | None: The created user or None on uniqueness violation.
        """
        if password_hash is None:
            password_hash = generate_password_hash("changeme")

        with self.Session() as session:
            try:
                user = User(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    age=age,
                    password_hash=password_hash,
                )
                session.add(user)
                session.commit()
                return user
            except Exception as exc:
                logger.exception("Failed to add user '%s': %s", username, exc)
                session.rollback()
                return None

    def update_user(self, user_id: int, updated_data: dict) -> User | None:
        """
        Update arbitrary user fields (e.g. email, password_hash).

        Args:
            user_id (int): ID of the user.
            updated_data (dict): Keys matching User columns.

        Returns:
            User | None: The updated user object, or None if not found.
        """
        allowed = {
            "username",
            "email",
            "first_name",
            "last_name",
            "age",
            "password_hash",
        }

        with self.Session() as session:
            user = session.get(User, user_id)
            if not user:
                logger.warning("Update failed: User ID %d not found.", user_id)
                return None

            for key, value in updated_data.items():
                if key in allowed:
                    setattr(user, key, value)

            session.commit()
            return user

    def delete_user(self, user_id: int):
        """Delete a user by ID.

        Args:
            user_id (int): The user's ID.

        Returns:
            bool: True if deleted, False if not found.
        """
        with self.Session() as session:
            user = session.get(User, user_id)
            if not user:
                logger.warning("Delete failed: User ID %d not found.", user_id)
                return False
            session.delete(user)
            session.commit()
            return True

    def add_movie(
            self,
            user_id: int,
            movie_data: dict,
            planned: bool = True,
            watched: bool = False,
            favorite: bool = False,
    ):
        """
        Insert a movie if it does not yet exist and (re)link it to the user.

        Args:
            user_id (int): ID of the user.
            movie_data (dict): Data returned by ``fetch_movie``.
            planned (bool): Flag for 'watchlist'.
            watched (bool): Flag for 'watched'.
            favorite (bool): Flag for 'favorite'.

        Returns:
            Movie | None: The (existing or newly created) movie object,
                          or None if the user is not found.
        """
        with self.Session() as session:
            user = session.get(User, user_id)
            if not user:
                logger.warning("Add movie failed: User ID %d not found.", user_id)
                return None

            stmt = select(Movie).where(
                Movie.title == movie_data["title"],
                Movie.year == movie_data["year"],
            )
            movie = session.execute(stmt).scalar_one_or_none()

            if movie is None:
                movie = Movie(
                    title=movie_data["title"],
                    director=movie_data.get("director"),
                    year=movie_data.get("year"),
                    genre=movie_data.get("genre"),
                    poster_url=movie_data.get("poster_url"),
                    imdb_rating=movie_data.get("imdb_rating"),
                )
                session.add(movie)
                session.flush()

            link = (
                session.query(UserMovie)
                .filter_by(user_id=user_id, movie_id=movie.id)
                .one_or_none()
            )
            if link is None:
                link = UserMovie(
                    user_id=user_id,
                    movie_id=movie.id,
                    is_planned=planned,
                    is_watched=watched,
                    is_favorite=favorite,
                )
                session.add(link)
            else:
                link.is_planned = planned or link.is_planned
                link.is_watched = watched or link.is_watched
                link.is_favorite = favorite or link.is_favorite

            session.commit()
            session.refresh(movie)
            return movie

    def update_movie(self, movie_id: int, updated_data: dict) -> Movie | None:
        """
        Update selected movie columns (title, director, year, genre, poster_url, imdb_rating).

        Args:
            movie_id (int): ID of the movie row.
            updated_data (dict): Field names + new values.

        Returns:
            Movie | None: The updated movie object or None if not found.
        """
        allowed = {
            "title",
            "director",
            "year",
            "genre",
            "poster_url",
            "imdb_rating",
        }

        with self.Session() as session:
            movie = session.get(Movie, movie_id)
            if not movie:
                logger.warning("Update failed: Movie ID %d not found.", movie_id)
                return None

            for key, val in updated_data.items():  # ➊
                if key in allowed:  # ➋
                    setattr(movie, key, val)

            session.commit()  # ➌
            return movie

    def delete_movie(self, movie_id: int):
        """Delete a movie by its ID.

        Args:
            movie_id (int): The movie's ID.

        Returns:
            bool: True if deleted, False if not found.
        """
        with self.Session() as session:
            movie = session.get(Movie, movie_id)
            if not movie:
                logger.warning("Delete failed: Movie ID %d not found.", movie_id)
                return False
            session.delete(movie)
            session.commit()
            return True

    def add_review(self, user_id: int, movie_id: int, review_data: dict):
        """Add a review for a movie by a user.

        Args:
            user_id (int): ID of the user.
            movie_id (int): ID of the movie.
            review_data (dict): Review text and user rating.

        Returns:
            Review | None: The created review or None if user/movie not found.
        """
        with self.Session() as session:
            user = session.get(User, user_id)
            movie = session.get(Movie, movie_id)

            if not user or not movie:
                logger.warning(
                    "Add review failed: user_id=%d or movie_id=%d not found.",
                    user_id, movie_id
                )
                return None

            review = Review(
                user_id=user_id,
                movie_id=movie_id,
                text=review_data.get("text"),
                user_rating=review_data.get("user_rating")
            )

            session.add(review)
            try:
                session.commit()
                session.refresh(review)
                return review
            except Exception as e:
                logger.error(
                    "Failed to add review: user_id=%d, movie_id=%d, error=%s",
                    user_id, movie_id, e
                )
                session.rollback()
                raise

    def get_reviews_for_movie(self, movie_id: int):
        """Return all reviews for a given movie, including user data.

        Args:
            movie_id (int): The movie's ID.

        Returns:
            list[Review]: All reviews for the movie with user data preloaded.
        """
        with self.Session() as session:
            stmt = select(Review).options(joinedload(Review.user)).where(Review.movie_id == movie_id)
            result = session.execute(stmt)
            return result.scalars().all()

    def get_reviews_by_user(self, user_id: int):
        """Return all reviews written by a given user.

        Args:
            user_id (int): The user's ID.

        Returns:
            list[Review]: All reviews by the user.
        """
        with self.Session() as session:
            stmt = select(Review).options(joinedload(Review.movie)).where(Review.user_id == user_id)
            result = session.execute(stmt)
            return result.scalars().all()

    def update_review(self, review_id: int, updated_data: dict):
        """Update the content or rating of a review.

        Args:
            review_id (int): The review's ID.
            updated_data (dict): Updated fields.

        Returns:
            Review | None: Updated review or None if not found.
        """
        with self.Session() as session:
            review = session.get(Review, review_id)
            if not review:
                logger.warning("Update failed: Review ID %d not found.", review_id)
                return None

            review.text = updated_data.get("text", review.text)
            review.user_rating = updated_data.get("user_rating", review.user_rating)

            session.commit()
            session.refresh(review)
            return review

    def delete_review(self, review_id: int):
        """Delete a review from the database.

        Args:
            review_id (int): The review's ID.

        Returns:
            bool: True if deleted, False if not found.
        """
        with self.Session() as session:
            review = session.get(Review, review_id)
            if not review:
                logger.warning("Delete failed: Review ID %d not found.", review_id)
                return False
            session.delete(review)
            session.commit()
            return True
