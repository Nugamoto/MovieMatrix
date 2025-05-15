import os
import sys

# --------------------------- Environment Setup --------------------------- #

# Set testing environment and default values before anything else
os.environ["FLASK_ENV"] = "testing"
os.environ.setdefault("OMDB_API_KEY", "test_dummy_key")

# Ensure project root is available in sys.path for all imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from datamanager.models import Base
from app import create_app

# --------------------------- Constants --------------------------- #

TEST_DB_PATH = "test_moviematrix.sqlite"
TEST_DB_URI = f"sqlite:///{TEST_DB_PATH}"


# --------------------------- Fixtures --------------------------- #

@pytest.fixture(scope="session")
def app():
    """
    Create and configure a new app instance for the test session.
    """
    app = create_app("TestingConfig")
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = TEST_DB_URI

    # Create all database tables using the app's engine
    engine = app.data_manager.engine
    Base.metadata.create_all(bind=engine)

    return app


@pytest.fixture
def client(app):
    """
    Return a test client for the Flask app.
    """
    with app.test_client() as client:
        yield client


@pytest.fixture
def data_manager(app):
    """
    Provide access to the data manager from the current app instance.
    """
    return app.data_manager


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    """
    Automatically remove the test database file after all tests.
    """
    yield
    try:
        os.remove(TEST_DB_PATH)
    except FileNotFoundError:
        pass
