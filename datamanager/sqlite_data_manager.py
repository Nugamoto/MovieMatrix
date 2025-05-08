from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from data_manager_interface import DataManagerInterface
from datamanager.models import User, Movie


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