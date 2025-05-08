from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from data_manager_interface import DataManagerInterface
from datamanager.models import User


class SQLiteDataManager(DataManagerInterface):
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def get_all_users(self):
        with self.Session() as session:
            users = session.query(User).all()
            return users
