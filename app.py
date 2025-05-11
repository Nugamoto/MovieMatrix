import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import SQLAlchemyError

from clients.omdb_client import fetch_movie
from datamanager.sqlite_data_manager import SQLiteDataManager
from helpers import (
    is_valid_username,
    get_user_by_id,
    get_movie_by_id,
    get_review_by_id,
    is_valid_year,
    is_valid_rating,
    normalize_rating,
)

# Load environment variables
load_dotenv()

# Flask setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")

# Data manager setup
DB_FILENAME = "moviematrix.sqlite"
if os.environ.get("FLASK_ENV") == "testing":
    DB_FILENAME = "test_moviematrix.sqlite"

data_manager = SQLiteDataManager(f"sqlite:///{DB_FILENAME}")

# Logging setup
if not os.path.exists("logs"):
    os.mkdir("logs")

file_handler = RotatingFileHandler("logs/app.log", maxBytes=10240, backupCount=3)
file_handler.setFormatter(logging.Formatter(
    "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
))
file_handler.setLevel(logging.INFO)

logger = logging.getLogger()
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/users")
def list_users():
    users = data_manager.get_all_users()
    return render_template("users.html", users=users)


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not is_valid_username(name):
            flash("Please enter a valid username.")
            logger.warning("Invalid username submitted: '%s'", name)
            return redirect(request.url)

        try:
            data_manager.add_user(name)
            logger.info("User added: '%s'", name)
            flash(f"User '{name}' was added.")
            return redirect(url_for("list_users"))
        except SQLAlchemyError as e:
            logger.error("Database error while adding user '%s': %s", name, str(e))
            flash("An error occurred while adding the user.")
            return redirect(request.url)

    return render_template("add_user.html")


@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash(f"User with ID {user_id} not found.")
        logger.warning("Attempted to delete non-existent user ID: %d", user_id)
        return redirect(url_for("list_users"))

    data_manager.delete_user(user_id)
    logger.info("User deleted: ID %d", user_id)
    flash(f"User '{user.name}' was deleted.")
    return redirect(url_for("list_users"))


@app.route("/users/<int:user_id>")
def user_movies(user_id):
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash(f"User with ID {user_id} not found.")
        logger.warning("User ID %d not found when accessing movies", user_id)
        return redirect(url_for("list_users"))

    movies = data_manager.get_user_movies(user_id)
    return render_template("user_movies.html", user=user, movies=movies)


@app.route('/users/<int:user_id>/add_movie', methods=["GET", "POST"])
def add_movie(user_id):
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash(f"User with ID {user_id} not found.")
        logger.warning("Add movie failed: user ID %d not found", user_id)
        return redirect(url_for("list_users"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        year = request.form.get("year", "").strip()

        if not title:
            flash("Please provide a movie title.")
            logger.warning("Add movie failed: empty title")
            return redirect(request.url)

        movie_data = fetch_movie(title, year)

        if not movie_data:
            flash(f"No movie found with title '{title}'.")
            logger.warning("OMDb returned no result for '%s' (%s)", title, year)
            return redirect(request.url)

        data_manager.add_movie(user_id, movie_data)
        logger.info("Movie '%s' added to user %d via OMDb", movie_data['title'], user_id)
        flash(f"Movie '{movie_data['title']}' added to {user.name}'s list.")
        return redirect(url_for("user_movies", user_id=user_id))

    return render_template("add_movie.html", user=user)


@app.route("/users/<int:user_id>/update_movie/<int:movie_id>", methods=["GET", "POST"])
def update_movie(user_id, movie_id):
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash(f"User with ID {user_id} not found.")
        logger.warning("Update movie failed: user ID %d not found", user_id)
        return redirect(url_for("list_users"))

    movies = data_manager.get_user_movies(user_id)
    movie = get_movie_by_id(movies, movie_id)
    if not movie:
        flash(f"Movie with ID {movie_id} not found.")
        logger.warning("Movie ID %d not found for user ID %d", movie_id, user_id)
        return redirect(url_for("user_movies", user_id=user_id))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        director = request.form.get("director", "").strip()
        year = request.form.get("year", "").strip()
        rating = request.form.get("rating", "").strip()

        if year and not is_valid_year(year):
            flash(f"'{year}' is not a valid year.")
            logger.warning("Invalid year during update: '%s'", year)
            return redirect(request.url)

        if rating and not is_valid_rating(rating):
            flash(f"'{rating}' is not a valid rating.")
            logger.warning("Invalid rating during update: '%s'", rating)
            return redirect(request.url)

        updated_data = {
            "title": title,
            "director": director,
            "year": year,
            "rating": normalize_rating(rating) if rating else None,
        }

        data_manager.update_movie(movie_id, updated_data)
        logger.info("Movie updated: ID %d by user %d", movie_id, user_id)
        flash(f"Movie '{title}' was updated.")
        return redirect(url_for("user_movies", user_id=user_id))

    return render_template("edit_movie.html", user=user, movie=movie)


@app.route("/users/<int:user_id>/delete_movie/<int:movie_id>", methods=["POST"])
def delete_movie(user_id, movie_id):
    movie = get_movie_by_id(data_manager.get_user_movies(user_id), movie_id)
    if not movie:
        flash(f"Movie with ID {movie_id} not found.")
        logger.warning("Delete failed: movie ID %d not found", movie_id)
        return redirect(url_for("user_movies", user_id=user_id))

    data_manager.delete_movie(movie_id)
    logger.info("Movie deleted: ID %d by user %d", movie_id, user_id)
    flash(f"Movie '{movie.title}' was deleted.")
    return redirect(url_for("user_movies", user_id=user_id))


@app.route("/users/<int:user_id>/reviews")
def user_reviews(user_id):
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash(f"User with ID {user_id} not found.")
        logger.warning("User ID %d not found when accessing reviews", user_id)
        return redirect(url_for("list_users"))

    reviews = data_manager.get_reviews_by_user(user_id)
    return render_template("user_reviews.html", user=user, reviews=reviews)


@app.route("/movies/<int:movie_id>/reviews")
def movie_reviews(movie_id):
    movies = data_manager.get_all_movies()
    movie = get_movie_by_id(movies, movie_id)
    if not movie:
        flash(f"Movie with ID {movie_id} not found.")
        logger.warning("Movie ID %d not found when accessing reviews", movie_id)
        return redirect(url_for("list_users"))

    reviews = data_manager.get_reviews_for_movie(movie_id)
    user_id = movie.user_id
    return render_template("movie_reviews.html", movie=movie, reviews=reviews, user_id=user_id)


@app.route("/users/<int:user_id>/movies/<int:movie_id>/add_review", methods=["GET", "POST"])
def add_review(user_id, movie_id):
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    movie = get_movie_by_id(data_manager.get_all_movies(), movie_id)

    if not user or not movie:
        flash("User or movie not found.")
        logger.warning("Add review failed: user_id=%d, movie_id=%d", user_id, movie_id)
        return redirect(url_for("list_users"))

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        rating = request.form.get("user_rating", "").strip()

        if not text:
            flash("Review text cannot be empty.")
            logger.warning("Review text missing in add_review for user_id=%d", user_id)
            return redirect(request.url)

        if not is_valid_rating(rating):
            flash("Invalid rating. Please enter a value between 0.0 and 10.0.")
            logger.warning("Invalid rating input in add_review: '%s'", rating)
            return redirect(request.url)

        review_data = {
            "text": text,
            "user_rating": normalize_rating(rating),
        }

        data_manager.add_review(user_id, movie_id, review_data)
        logger.info("Review added by user %d for movie %d", user_id, movie_id)
        flash("Review successfully added.")
        return redirect(url_for("movie_reviews", movie_id=movie_id, user_id=user_id))

    return render_template("add_review.html", user=user, movie=movie)


@app.route("/users/<int:user_id>/edit_review/<int:review_id>", methods=["GET", "POST"])
def edit_review(user_id, review_id):
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash(f"User with ID {user_id} not found.")
        return redirect(url_for("list_users"))

    reviews = data_manager.get_reviews_by_user(user_id)
    review = get_review_by_id(reviews, review_id)
    if not review:
        flash(f"Review with ID {review_id} not found.")
        logger.warning("Edit failed: review ID %d not found", review_id)
        return redirect(url_for("user_reviews", user_id=user_id))

    movies = data_manager.get_user_movies(user_id)
    movie = get_movie_by_id(movies, review.movie_id)

    next_url = request.args.get("next")

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        rating = request.form.get("user_rating", "").strip()

        if not text:
            flash("Review text cannot be empty.")
            logger.warning("Empty review text during edit_review for ID %d", review_id)
            return redirect(request.url)

        if not is_valid_rating(rating):
            flash("Invalid rating. Please enter a number between 0.0 and 10.0.")
            logger.warning("Invalid rating input in edit_review: '%s'", rating)
            return redirect(request.url)

        updated_data = {
            "text": text,
            "user_rating": normalize_rating(rating),
        }

        data_manager.update_review(review_id, updated_data)
        logger.info("Review updated: ID %d", review_id)
        flash(f"Review for '{movie.title}' updated.")
        return redirect(next_url) if next_url else redirect(url_for("user_reviews", user_id=user_id))

    return render_template("edit_review.html", user=user, movie=movie, review=review)


@app.route("/users/<int:user_id>/delete_review/<int:review_id>", methods=["POST"])
def delete_review(user_id, review_id):
    reviews = data_manager.get_reviews_by_user(user_id)
    review = get_review_by_id(reviews, review_id)

    if not review:
        flash(f"Review with ID {review_id} not found.")
        logger.warning("Delete failed: review ID %d not found", review_id)
        return redirect(url_for("user_reviews", user_id=user_id))

    data_manager.delete_review(review_id)
    logger.info("Review deleted: ID %d by user %d", review_id, user_id)
    flash("Review deleted.")
    return redirect(url_for("user_reviews", user_id=user_id))


@app.errorhandler(404)
def page_not_found(e):
    logger.warning("404 error: %s", request.path)
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    logger.error("500 error occurred: %s", str(e))
    return render_template("500.html"), 500


@app.errorhandler(SQLAlchemyError)
def handle_sqlalchemy_error(e):
    logger.error("SQLAlchemy error: %s", e)
    flash("A database error occurred. Please try again later.")
    return redirect(url_for("list_users"))


@app.errorhandler(Exception)
def handle_unexpected_error(e):
    logger.exception("Unhandled exception:")
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)

