import os
from pathlib import Path

BASE_DIR = Path(__file__).parent


class BaseConfig:
    """
    Base configuration with settings common to all environments.
    """
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    LOG_DIR = BASE_DIR / "logs"
    LOG_DIR.mkdir(exist_ok=True)

    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{BASE_DIR / 'moviematrix.sqlite'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):
    """
    Development configuration: debug enabled.
    """
    DEBUG = True
    FLASK_ENV = "development"


class ProductionConfig(BaseConfig):
    """
    Production configuration: debug disabled.
    """
    DEBUG = False
    FLASK_ENV = "production"


class TestingConfig(BaseConfig):
    """
    Testing configuration: in-memory database, testing mode enabled.
    """
    TESTING = True
    FLASK_ENV = "testing"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
