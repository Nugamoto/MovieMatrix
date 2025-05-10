import os
import sys

import pytest

# Set testing environment before Flask app is imported
os.environ["FLASK_ENV"] = "testing"

# Add root project directory to sys.path so we can import app and datamanager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- Import after environment setup ---
from app import app
from sqlalchemy import create_engine
from datamanager.models import Base
from datamanager.sqlite_data_manager import SQLiteDataManager

# --- Ensure test database schema exists ---
TEST_DB_PATH = "test_moviematrix.sqlite"
engine = create_engine(f"sqlite:///{TEST_DB_PATH}")
Base.metadata.create_all(engine)


# --- Fixtures ---

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def data_manager():
    return SQLiteDataManager(f"sqlite:///{TEST_DB_PATH}")


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    """Remove the test database file after the test session ends."""
    yield
    try:
        os.remove(TEST_DB_PATH)
    except FileNotFoundError:
        pass
