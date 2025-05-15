"""
Pytest configuration and fixtures for MovieMatrix application tests.

This module sets up the testing environment, application factory,
client and data manager fixtures, and helper utilities for user
registration and cleanup.
"""
import os
import sys
import uuid

import pytest

# --------------------------- Environment Setup --------------------------- #
# Set testing environment and default values before anything else
os.environ["FLASK_ENV"] = "testing"
os.environ.setdefault("OMDB_API_KEY", "test_dummy_key")

# Ensure project root is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from datamanager.models import Base

# --------------------------- Constants --------------------------- #
TEST_DB_PATH = "test_moviematrix.sqlite"
TEST_DB_URI = f"sqlite:///{TEST_DB_PATH}"


# --------------------------- Fixtures --------------------------- #

@pytest.fixture(scope="session")
def app():
    """
    Create and configure a new Flask app instance for tests.

    Applies TestingConfig, enables TESTING mode, and initializes the database.
    Returns:
        Flask app: The configured application.
    """
    app = create_app("TestingConfig")
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = TEST_DB_URI

    # Create tables
    engine = app.data_manager.engine
    Base.metadata.create_all(bind=engine)

    return app


@pytest.fixture
def client(app):
    """
    Provide a Flask test client for sending HTTP requests.

    Yields:
        FlaskClient: A test client for the app.
    """
    with app.test_client() as client:
        yield client


@pytest.fixture
def data_manager(app):
    """
    Provide the SQLiteDataManager instance from the Flask app.

    Args:
        app: The Flask application instance.
    Returns:
        SQLiteDataManager: The data manager for DB operations.
    """
    return app.data_manager


# ---------------------- Helper Fixture ---------------------- #

@pytest.fixture
def register_user_and_login(client):
    """
    Helper fixture to register a new user via form and log them in.

    Returns:
        function: Caller function accepting prefix, first_name, last_name, age.
    Usage:
        user = register_user_and_login(prefix="movie")
    """

    def _create(prefix="user", first_name="Test", last_name="User", age=30):
        unique = uuid.uuid4().hex[:6]
        username = f"{prefix}_{unique}"
        email = f"{username}@example.com"
        password = "secret123"
        # Register
        form = {
            "username": username,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "age": str(age),
            "password": password,
            "confirm_password": password,
        }
        response = client.post(
            "/users/add",
            data=form,
            follow_redirects=True
        )
        assert response.status_code in (200, 302)
        # Login
        response = client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True
        )
        assert response.status_code == 200
        return {"username": username, "email": email, "password": password}

    return _create


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    """
    Remove the temporary test database file after tests complete.
    """
    yield
    try:
        os.remove(TEST_DB_PATH)
    except FileNotFoundError:
        pass
