from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from data_manager_interface import DataManagerInterface


class SQLiteDataManager(DataManagerInterface):
    def __init__(self, db_url: str):
        self.engine = create_engine(self.db)
        self.session = sessionmaker(bind=self.engine)
