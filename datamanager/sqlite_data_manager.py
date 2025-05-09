from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from data_manager_interface import DataManagerInterface
from datamanager.models import User, Movie, Review


class SQLiteDataManager(DataManagerInterface):
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def get_all_users(self):
        """Return all users from the database.

        Returns:
            list[User]: A list of all users.
        """
        with self.Session() as session:
            result = session.execute(select(User))
            return result.scalars().all()

    def get_user_movies(self, user_id: int):
        """Return all movies that belong to a specific user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list[Movie]: List of movies owned by the user.
        """
        with self.Session() as session:
            result = session.execute(
                select(Movie).where(Movie.user_id == user_id)
            )
            return result.scalars().all()

    def add_user(self, name: str):
        """Add a new user to the database.

        Args:
            name (str): Name of the user.

        Returns:
            User: The created user object.
        """
        with self.Session() as session:
            user = User(name=name)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def update_user(self, user_id: int, new_name: str):
        """Update the name of a user by their ID.

        Args:
            user_id (int): The user's ID.
            new_name (str): The new name.

        Returns:
            User | None: The updated user object or None if not found.
        """
        with self.Session() as session:
            user = session.get(User, user_id)
            if not user:
                return None
            user.name = new_name
            session.commit()
            session.refresh(user)
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
                return False
            session.delete(user)
            session.commit()
            return True

    def add_movie(self, user_id: int, movie_data: dict):
        """Add a movie to a user's movie list.

        Args:
            user_id (int): ID of the user.
            movie_data (dict): Movie data (title, director, year, rating).

        Returns:
            Movie | None: The created movie object, or None if user not found.
        """
        with self.Session() as session:
            user = session.get(User, user_id)
            if not user:
                return None

            movie = Movie(
                title=movie_data.get("title"),
                director=movie_data.get("director"),
                year=movie_data.get("year"),
                rating=movie_data.get("rating"),
                user_id=user_id
            )

            session.add(movie)
            session.commit()
            session.refresh(movie)
            return movie

    def update_movie(self, movie_id: int, updated_data: dict):
        """Update a movie's details.

        Args:
            movie_id (int): The movie's ID.
            updated_data (dict): Fields to update.

        Returns:
            Movie | None: The updated movie, or None if not found.
        """
        with self.Session() as session:
            movie = session.get(Movie, movie_id)
            if not movie:
                return None

            movie.title = updated_data.get("title", movie.title)
            movie.director = updated_data.get("director", movie.director)
            movie.year = updated_data.get("year", movie.year)
            movie.rating = updated_data.get("rating", movie.rating)

            session.commit()
            session.refresh(movie)
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
                return None

            review = Review(
                user_id=user_id,
                movie_id=movie_id,
                text=review_data.get("text"),
                user_rating=review_data.get("user_rating")
            )

            session.add(review)
            session.commit()
            session.refresh(review)
            return review

    def get_reviews_for_movie(self, movie_id: int):
        """Return all reviews for a given movie.

        Args:
            movie_id (int): The movie's ID.

        Returns:
            list[Review]: All reviews for the movie.
        """
        with self.Session() as session:
            result = session.execute(
                select(Review).where(Review.movie_id == movie_id)
            )
            return result.scalars().all()

    def get_reviews_by_user(self, user_id: int):
        """Return all reviews written by a given user.

        Args:
            user_id (int): The user's ID.

        Returns:
            list[Review]: All reviews by the user.
        """
        with self.Session() as session:
            result = session.execute(
                select(Review).where(Review.user_id == user_id)
            )
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
                return False
            session.delete(review)
            session.commit()
            return True
