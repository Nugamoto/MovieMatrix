import os
import sys

import pytest

# Add root directory to import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datamanager.sqlite_data_manager import SQLiteDataManager

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def data_manager():
    return SQLiteDataManager("sqlite:///moviematrix.sqlite")
