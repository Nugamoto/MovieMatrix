from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from data_manager_interface import DataManagerInterface
from datamanager.models import User, Movie


class SQLiteDataManager(DataManagerInterface):
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def get_all_users(self):
        with self.Session() as session:
            users = session.query(User).all()
            return users

    def get_user_movies(self, user_id: int):
        with self.Session() as session:
            movies = session.query(Movie).filter(Movie.user_id == user_id).all()
            return movies
