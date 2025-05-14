import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager
from sqlalchemy.exc import SQLAlchemyError

import config
from datamanager.sqlite_data_manager import SQLiteDataManager


def create_app(config_name: str | None = None) -> Flask:
    """
    Application factory: create and configure the Flask app.

    :param config_name: Name of the config class (e.g., 'DevelopmentConfig')
    :return: Configured Flask app instance
    """
    if config_name is None:
        env = os.getenv("FLASK_ENV", "development")
        config_name = f"{env.capitalize()}Config"

    app = Flask(__name__)
    app.config.from_object(getattr(config, config_name))

    # Set up logging
    log_dir = app.config["LOG_DIR"]
    file_handler = RotatingFileHandler(
        log_dir / "app.log", maxBytes=10_240, backupCount=3
    )
    file_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )
    )
    file_handler.setLevel(logging.INFO)

    if not app.logger.handlers:
        app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    # Initialize data manager
    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    data_manager = SQLiteDataManager(db_uri)
    app.data_manager = data_manager

    # Configure Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = "core.login"
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        return data_manager.get_user_by_id(int(user_id))

    # Register blueprints
    from blueprints.core import core_bp
    from blueprints.movies import movies_bp
    from blueprints.users import users_bp
    from blueprints.reviews import reviews_bp

    app.register_blueprint(core_bp)
    app.register_blueprint(movies_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(reviews_bp)

    # Register error handlers
    register_errorhandlers(app)

    return app


def register_errorhandlers(app: Flask) -> None:
    """
    Register application-wide error handlers.

    :param app: The Flask application instance
    """

    @app.errorhandler(404)
    def not_found(error):
        app.logger.warning("404 error: %s", request.path)
        return render_template("404.html"), 404

    @app.errorhandler(403)
    def forbidden(error):
        app.logger.warning("403 error: %s", request.path)
        flash("Access forbidden.", "warning")
        return redirect(url_for("users.list_users"))

    @app.errorhandler(SQLAlchemyError)
    def db_error(error):
        app.logger.error("Database error: %s", error)
        flash("A database error occurred.", "danger")
        return redirect(url_for("users.list_users"))

    @app.errorhandler(Exception)
    def unexpected_error(error):
        app.logger.exception("Unhandled exception at %s", request.path)
        return render_template("500.html"), 500


if __name__ == "__main__":
    create_app().run()
