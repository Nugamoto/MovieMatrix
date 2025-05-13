"""
SQLiteDataManager
-----------------
Concrete DataManagerInterface implementation using SQLite + SQLAlchemy.

Provides CRUD operations for users, movies, reviews and the user_movies link
table.  Each method opens a short-lived session (context manager) to keep
transactions explicit and connections short-lived.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, sessionmaker
from werkzeug.security import generate_password_hash

from datamanager.data_manager_interface import DataManagerInterface
from datamanager.models import Movie, Review, User, UserMovie

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
#                            helper / constants                               #
# --------------------------------------------------------------------------- #
USER_UPDATE_FIELDS = {
    "username",
    "email",
    "first_name",
    "last_name",
    "age",
    "password_hash",
}
MOVIE_UPDATE_FIELDS = {
    "title",
    "director",
    "year",
    "genre",
    "poster_url",
    "imdb_rating",
}
REVIEW_UPDATE_FIELDS = {"title", "text", "user_rating"}


class SQLiteDataManager(DataManagerInterface):
    """SQLite implementation of DataManagerInterface."""

    # --------------------------------------------------------------------- #
    #                                setup                                  #
    # --------------------------------------------------------------------- #

    def __init__(self, db_url: str) -> None:
        self.engine = create_engine(db_url, future=True)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    # --------------------------------------------------------------------- #
    #                                user                                   #
    # --------------------------------------------------------------------- #

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Return a user object by ID, or None if not found."""
        with self.Session() as session:
            return session.get(User, user_id)

    def get_user_by_username(self, username: str):
        """Return a user object matching the given username, or None."""
        with self.Session() as session:
            stmt = select(User).where(User.username == username)
            return session.execute(stmt).scalar_one_or_none()

    def get_all_users(self) -> List[User]:
        """Return all user records from the database."""
        with self.Session() as session:
            return session.execute(select(User)).scalars().all()

    def add_user(
            self,
            username: str,
            email: str,
            first_name: str,
            password_hash: Optional[str] = None,
            last_name: Optional[str] = None,
            age: Optional[int] = None,
    ) -> Optional[User]:
        """Create a user with the provided data and return the object or None on failure."""
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
            except IntegrityError as exc:
                logger.warning(
                    "Uniqueness violation while adding user '%s': %s", username, exc
                )
                session.rollback()
                return None

    def update_user(self, user_id: int, updated_data: Dict[str, Any]) -> Optional[User]:
        """Update fields of a user and return the updated object or None if not found."""
        with self.Session() as session:
            user = session.get(User, user_id)
            if not user:
                logger.warning("Update failed: User ID %d not found.", user_id)
                return None

            for key, value in updated_data.items():
                if key in USER_UPDATE_FIELDS:
                    setattr(user, key, value)

            session.commit()
            return user

    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID; return True if successful, False if not found."""
        with self.Session() as session:
            user = session.get(User, user_id)
            if not user:
                logger.warning("Delete failed: User ID %d not found.", user_id)
                return False
            session.delete(user)
            session.commit()
            return True

    # --------------------------------------------------------------------- #
    #                                movie                                  #
    # --------------------------------------------------------------------- #

    def get_movie_by_id(self, movie_id: int) -> Optional[Movie]:
        """Return a movie object by ID, or None if not found."""
        with self.Session() as session:
            return session.get(Movie, movie_id)

    def get_all_movies(self) -> List[Movie]:
        """Return all movie records from the database."""
        with self.Session() as session:
            return session.execute(select(Movie)).scalars().all()

    def get_movies_by_user(self, user_id: int) -> List[Movie]:
        """Return all movies linked to a given user."""
        with self.Session() as session:
            stmt = (
                select(Movie)
                .join(UserMovie, Movie.id == UserMovie.movie_id)
                .where(UserMovie.user_id == user_id)
            )
            return session.execute(stmt).scalars().all()

    def add_movie(
            self,
            user_id: int,
            movie_data: Dict[str, Any],
            planned: bool = True,
            watched: bool = False,
            favorite: bool = False,
    ) -> Optional[Movie]:
        """Add or link a movie to a user and return the Movie object."""
        with self.Session() as session:
            user = session.get(User, user_id)
            if not user:
                logger.warning("Add movie failed: User ID %d not found.", user_id)
                return None

            movie = (
                session.execute(
                    select(Movie).where(
                        Movie.title == movie_data["title"],
                        Movie.year == movie_data["year"],
                    )
                )
                .scalar_one_or_none()
            )

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
                session.flush()  # generate ID for link

            link = (
                session.query(UserMovie)
                .filter_by(user_id=user_id, movie_id=movie.id)
                .one_or_none()
            )
            if link is None:
                session.add(
                    UserMovie(
                        user_id=user_id,
                        movie_id=movie.id,
                        is_planned=planned,
                        is_watched=watched,
                        is_favorite=favorite,
                    )
                )
            else:
                link.is_planned |= planned
                link.is_watched |= watched
                link.is_favorite |= favorite

            session.commit()
            return movie

    def update_movie(
            self, movie_id: int, updated_data: Dict[str, Any]
    ) -> Optional[Movie]:
        """Update fields of a movie and return the updated object or None."""
        with self.Session() as session:
            movie = session.get(Movie, movie_id)
            if not movie:
                logger.warning("Update failed: Movie ID %d not found.", movie_id)
                return None

            for key, val in updated_data.items():
                if key in MOVIE_UPDATE_FIELDS:
                    setattr(movie, key, val)

            session.commit()
            return movie

    def delete_movie(self, movie_id: int) -> bool:
        """Delete a movie by ID; return True if successful, False if not found."""
        with self.Session() as session:
            movie = session.get(Movie, movie_id)
            if not movie:
                logger.warning("Delete failed: Movie ID %d not found.", movie_id)
                return False
            session.delete(movie)
            session.commit()
            return True

    # --------------------------------------------------------------------- #
    #                                review                                 #
    # --------------------------------------------------------------------- #

    def get_review_by_id(self, review_id: int) -> Optional[Review]:
        """Return a review object by ID, or None if not found."""
        with self.Session() as session:
            return session.get(Review, review_id)

    def get_review_detail(self, review_id: int):
        """Return a review with related user and movie data by ID."""
        with self.Session() as session:
            stmt = (
                select(Review)
                .options(
                    joinedload(Review.movie),
                    joinedload(Review.user),
                )
                .where(Review.id == review_id)
            )
            return session.execute(stmt).scalar_one_or_none()

    def get_reviews_for_movie(self, movie_id: int) -> List[Review]:
        """Return all reviews for a specific movie."""
        with self.Session() as session:
            stmt = (
                select(Review)
                .options(joinedload(Review.user))
                .where(Review.movie_id == movie_id)
            )
            return session.execute(stmt).scalars().all()

    def get_reviews_by_user(self, user_id: int) -> List[Review]:
        """Return all reviews written by a specific user."""
        with self.Session() as session:
            stmt = (
                select(Review)
                .options(joinedload(Review.movie))
                .where(Review.user_id == user_id)
            )
            return session.execute(stmt).scalars().all()

    def add_review(
            self, user_id: int, movie_id: int, review_data: Dict[str, Any]
    ) -> Optional[Review]:
        """Create and return a new review, or None if user or movie not found."""
        with self.Session() as session:
            if not (session.get(User, user_id) and session.get(Movie, movie_id)):
                logger.warning(
                    "Add review failed: user_id=%d or movie_id=%d not found.",
                    user_id,
                    movie_id,
                )
                return None

            review = Review(
                user_id=user_id,
                movie_id=movie_id,
                title=review_data.get("title"),
                text=review_data.get("text"),
                user_rating=review_data.get("user_rating"),
            )
            session.add(review)
            session.commit()
            return review

    def update_review(
            self, review_id: int, updated_data: Dict[str, Any]
    ) -> Optional[Review]:
        """Update fields of a review and return the updated object or None."""
        with self.Session() as session:
            review = session.get(Review, review_id)
            if not review:
                logger.warning("Update failed: Review ID %d not found.", review_id)
                return None

            for key, val in updated_data.items():
                if key in REVIEW_UPDATE_FIELDS:
                    setattr(review, key, val)

            session.commit()
            return review

    def delete_review(self, review_id: int) -> bool:
        """Delete a review by ID; return True if successful, False if not found."""
        with self.Session() as session:
            review = session.get(Review, review_id)
            if not review:
                logger.warning("Delete failed: Review ID %d not found.", review_id)
                return False
            session.delete(review)
            session.commit()
            return True
