from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from data_manager_interface import DataManagerInterface
from datamanager.models import User, Movie, Review


class SQLiteDataManager(DataManagerInterface):
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def get_all_users(self):
        """Return all users from the database."""
        with self.Session() as session:
            all_users = session.query(User).all()
            return all_users

    def get_user_movies(self, user_id: int):
        """Return all movies that belong to a specific user."""
        with self.Session() as session:
            movies = session.query(Movie).filter(Movie.user_id == user_id).all()
            return movies

    def add_user(self, name: str):
        """Add a new user to the database and return the user object."""
        with self.Session() as session:
            user = User(name=name)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def update_user(self, user_id: int, new_name: str):
        """Update the name of a user by their ID."""
        with self.Session() as session:
            user = session.query(User).get(user_id)
            if not user:
                return None
            user.name = new_name
            session.commit()
            session.refresh(user)
            return user

    def delete_user(self, user_id: int):
        """Delete a user by ID."""
        with self.Session() as session:
            user = session.query(User).get(user_id)
            if not user:
                return False
            session.delete(user)
            session.commit()
            return True

    def add_movie(self, user_id: int, movie_data: dict):
        """Add a movie to a user's movie list."""
        with self.Session() as session:
            user = session.query(User).get(user_id)
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
        """Update a movie's details."""
        with self.Session() as session:
            movie = session.query(Movie).get(movie_id)
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
        """Delete a movie by its ID."""
        with self.Session() as session:
            movie = session.query(Movie).get(movie_id)
            if not movie:
                return False
            session.delete(movie)
            session.commit()
            return True

    def add_review(self, user_id: int, movie_id: int, review_data: dict):
        """Add a review for a movie by a user."""
        with self.Session() as session:
            user = session.query(User).get(user_id)
            movie = session.query(Movie).get(movie_id)

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
