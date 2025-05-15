import os
import sys
import uuid

import pytest

# --------------------------- Environment Setup --------------------------- #
# Set testing environment and default values before anything else
os.environ["FLASK_ENV"] = "testing"
os.environ.setdefault("OMDB_API_KEY", "test_dummy_key")

# Ensure project root is available in sys.path for all imports
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


# ---------------------- Helper Fixture ---------------------- #
@pytest.fixture
def register_user_and_login(client):
    """
    Register a new user via the HTTP form and log them in.

    Usage:
        user = register_user_and_login(prefix="movie")
    Returns:
        A dict with keys 'id', 'username', 'email', 'password'.
    """

    def _create(prefix="user", first_name="Test", last_name="User", age=30):
        unique = uuid.uuid4().hex[:6]
        username = f"{prefix}_{unique}"
        email = f"{username}@example.com"
        password = "secret123"
        # Register user
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
        # Now login
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
    Automatically remove the test database file after all tests.
    """
    yield
    try:
        os.remove(TEST_DB_PATH)
    except FileNotFoundError:
        pass
