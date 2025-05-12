"""
MovieMatrix Flask application.

Features
--------
* User registration & deletion
* Managing movies (add, edit, delete) per user
* Writing, editing and deleting reviews
* SQLite backend via SQLAlchemy, OMDb API client for movie data
* Bootstrap-based HTML templates, server-side form validation

Run standalone with ``python app.py`` (development) or import a factory
function later for production WSGI servers.

Author: Your Name
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from clients.omdb_client import fetch_movie
from datamanager.sqlite_data_manager import SQLiteDataManager
from helpers import (
    get_movie_by_id,
    get_review_by_id,
    get_user_by_id,
    is_valid_email,
    is_valid_name,
    is_valid_rating,
    is_valid_username,
    is_valid_year,
    normalize_rating,
    passwords_match,
)

# ---------------------------------------------------------------------- #
#                           Flask & logging setup                        #
# ---------------------------------------------------------------------- #

load_dotenv()
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")

db_filename = (
    "test_moviematrix.sqlite"
    if os.getenv("FLASK_ENV") == "testing"
    else "moviematrix.sqlite"
)
data_manager = SQLiteDataManager(f"sqlite:///{db_filename}")

file_handler = RotatingFileHandler(LOG_DIR / "app.log", maxBytes=10240, backupCount=3)
file_handler.setFormatter(
    logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
)
file_handler.setLevel(logging.INFO)

logger = logging.getLogger()
if not logger.handlers:  # prevent duplicate handlers in debug reload
    logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------- #
#                               Routes                                   #
# ---------------------------------------------------------------------- #


@app.route("/")
def home():
    """Render static landing page."""
    return render_template("home.html")


@app.route("/users")
def list_users():
    """List all registered users."""
    users = data_manager.get_all_users()
    return render_template("users.html", users=users)


# ------------------------------ USERS --------------------------------- #


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    """Handle user registration form (GET) and submission (POST)."""
    if request.method == "POST":
        # --- Extract & validate ------------------------------------------------
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip() or None
        age_raw = request.form.get("age", "").strip()
        password = request.form.get("password", "")
        confirm_pw = request.form.get("confirm_password", "")

        if not is_valid_username(username):
            flash("Invalid username (3-30 chars, letters, digits, _).", "danger")
            return redirect(request.url)

        if not is_valid_email(email):
            flash("Invalid e-mail address.", "danger")
            return redirect(request.url)

        if not is_valid_name(first_name):
            flash("First name may only contain letters, spaces, - and '.", "danger")
            return redirect(request.url)

        if last_name and not is_valid_name(last_name):
            flash("Last name may only contain letters, spaces, - and '.", "danger")
            return redirect(request.url)

        if not passwords_match(password, confirm_pw):
            flash("Passwords do not match.", "danger")
            return redirect(request.url)

        # --- Persist -----------------------------------------------------------
        age = int(age_raw) if age_raw.isdigit() else None
        pw_hash = generate_password_hash(password)

        try:
            user_obj = data_manager.add_user(
                username,
                email,
                first_name,
                pw_hash,
                last_name,
                age,
            )
            if user_obj:
                flash(f"User “{username}” created.", "success")
            else:
                flash("Username or e-mail already exists.", "danger")
            return redirect(url_for("list_users"))
        except SQLAlchemyError as exc:
            logger.error("DB error while adding user '%s': %s", username, exc)
            flash("Database error while adding user.", "danger")
            return redirect(request.url)

    # GET
    return render_template("add_user.html")


@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id: int):
    """Delete a user and cascade their movies & reviews."""
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("list_users"))

    data_manager.delete_user(user_id)
    flash(f"User “{user.username}” deleted.", "success")
    return redirect(url_for("list_users"))


@app.route("/users/<int:user_id>")
def user_movies(user_id: int):
    """Show movie list for a given user."""
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("list_users"))

    movies = data_manager.get_movies_by_user(user_id)
    return render_template("user_movies.html", user=user, movies=movies)


# ------------------------------ MOVIES -------------------------------- #


@app.route("/users/<int:user_id>/add_movie", methods=["GET", "POST"])
def add_movie(user_id: int):
    """Add a movie to user's list via OMDb lookup."""
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("list_users"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        year = request.form.get("year", "").strip()
        planned = bool(request.form.get("planned"))
        watched = bool(request.form.get("watched"))
        favorite = bool(request.form.get("favorite"))

        if not title:
            flash("Movie title is required.", "danger")
            return redirect(request.url)

        movie_data = fetch_movie(title, year)
        if not movie_data:
            flash("No movie found.", "warning")
            return redirect(request.url)

        data_manager.add_movie(user_id, movie_data, planned, watched, favorite)
        flash(f"Movie “{movie_data['title']}” added.", "success")
        return redirect(url_for("user_movies", user_id=user_id))

    return render_template("add_movie.html", user=user)


@app.route("/users/<int:user_id>/update_movie/<int:movie_id>", methods=["GET", "POST"])
def update_movie(user_id: int, movie_id: int):
    """Edit movie meta-data (title, director, year, genre, IMDb rating)."""
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    movie = get_movie_by_id(data_manager.get_movies_by_user(user_id), movie_id)
    if not user or not movie:
        flash("User or movie not found.", "danger")
        return redirect(url_for("list_users"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        director = request.form.get("director", "").strip()
        year = request.form.get("year", "").strip()
        genre = request.form.get("genre", "").strip()
        imdb_rating = request.form.get("imdb_rating", "").strip()

        if year and not is_valid_year(year):
            flash("Invalid year.", "danger")
            return redirect(request.url)
        if imdb_rating and not is_valid_rating(imdb_rating):
            flash("IMDb rating must be 0-10.", "danger")
            return redirect(request.url)

        updated_data = {
            "title": title or movie.title,
            "director": director or movie.director,
            "year": year or movie.year,
            "genre": genre or movie.genre,
            "imdb_rating": normalize_rating(imdb_rating)
            if imdb_rating
            else movie.imdb_rating,
        }
        data_manager.update_movie(movie_id, updated_data)
        flash("Movie updated.", "success")
        return redirect(url_for("user_movies", user_id=user_id))

    return render_template("edit_movie.html", user=user, movie=movie)


@app.route("/users/<int:user_id>/delete_movie/<int:movie_id>", methods=["POST"])
def delete_movie(user_id: int, movie_id: int):
    """Remove a movie link (and possibly the movie) from a user."""
    movie = get_movie_by_id(data_manager.get_movies_by_user(user_id), movie_id)
    if not movie:
        flash("Movie not found.", "danger")
        return redirect(url_for("user_movies", user_id=user_id))

    data_manager.delete_movie(movie_id)
    flash("Movie deleted.", "success")
    return redirect(url_for("user_movies", user_id=user_id))


# ------------------------------ REVIEWS ------------------------------ #


@app.route("/users/<int:user_id>/reviews")
def user_reviews(user_id: int):
    """Display all reviews authored by a user."""
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash(f"User with ID {user_id} not found.")
        logger.warning("User ID %d not found when accessing reviews", user_id)
        return redirect(url_for("list_users"))

    reviews = data_manager.get_reviews_by_user(user_id)
    next_url = request.args.get("next") or request.referrer or url_for("user_movies", user_id=user_id)
    return render_template("user_reviews.html", user=user, reviews=reviews, next=next_url)


@app.route("/movies/<int:movie_id>/reviews")
def movie_reviews(movie_id: int):
    """List reviews for a movie; optional user_id enables 'Add Review' button."""
    movie = get_movie_by_id(data_manager.get_all_movies(), movie_id)
    if not movie:
        flash(f"Movie with ID {movie_id} not found.")
        logger.warning("Movie ID %d not found when accessing reviews", movie_id)
        return redirect(url_for("list_users"))

    reviews = data_manager.get_reviews_for_movie(movie_id)
    user_id = request.args.get("user_id", type=int)
    next_url = request.args.get("next") or url_for("list_users")

    return render_template(
        "movie_reviews.html",
        movie=movie,
        reviews=reviews,
        user_id=user_id,
        next_url=next_url,
    )


@app.route("/users/<int:user_id>/movies/<int:movie_id>/add_review", methods=["GET", "POST"])
def add_review(user_id: int, movie_id: int):
    """Add a new review (title, text, rating) for a movie."""
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    movie = get_movie_by_id(data_manager.get_all_movies(), movie_id)
    if not user or not movie:
        flash("User or movie not found.", "danger")
        return redirect(url_for("list_users"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        text = request.form.get("text", "").strip()
        rating = request.form.get("user_rating", "").strip()

        if not title or not text:
            flash("Title and text required.", "danger")
            return redirect(request.url)
        if not is_valid_rating(rating):
            flash("Rating must be 0-10.", "danger")
            return redirect(request.url)

        data_manager.add_review(
            user_id,
            movie_id,
            {"title": title, "text": text, "user_rating": normalize_rating(rating)},
        )
        flash("Review added.", "success")
        return redirect(url_for("movie_reviews", movie_id=movie_id, user_id=user_id))

    return render_template("add_review.html", user=user, movie=movie)


@app.route("/users/<int:user_id>/edit_review/<int:review_id>", methods=["GET", "POST"])
def edit_review(user_id: int, review_id: int):
    """Edit a user’s review (title, text, rating)."""
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    review = get_review_by_id(data_manager.get_reviews_by_user(user_id), review_id)
    if not user or not review:
        flash("User or review not found.", "danger")
        return redirect(url_for("list_users"))

    movie = get_movie_by_id(data_manager.get_movies_by_user(user_id), review.movie_id)
    next_url = request.args.get("next")

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        text = request.form.get("text", "").strip()
        rating = request.form.get("user_rating", "").strip()

        if not title or not text:
            flash("Title and text required.", "danger")
            return redirect(request.url)
        if not is_valid_rating(rating):
            flash("Rating must be 0-10.", "danger")
            return redirect(request.url)

        data_manager.update_review(
            review_id,
            {"title": title, "text": text, "user_rating": normalize_rating(rating)},
        )
        flash("Review updated.", "success")
        return redirect(next_url) if next_url else redirect(url_for("user_reviews", user_id=user_id))

    return render_template("edit_review.html", user=user, movie=movie, review=review)


@app.route("/users/<int:user_id>/delete_review/<int:review_id>", methods=["POST"])
def delete_review(user_id: int, review_id: int):
    """Delete a review authored by a user."""
    review = get_review_by_id(data_manager.get_reviews_by_user(user_id), review_id)
    if not review:
        flash("Review not found.", "danger")
        return redirect(url_for("user_reviews", user_id=user_id))

    data_manager.delete_review(review_id)
    flash("Review deleted.", "success")
    return redirect(url_for("user_reviews", user_id=user_id))


# --------------------------- Error handlers -------------------------- #


@app.errorhandler(404)
def page_not_found(e):
    """Render custom 404 page."""
    logger.warning("404 error: %s", request.path)
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    """Render custom 500 page."""
    logger.error("500 error occurred: %s", str(e))
    return render_template("500.html"), 500


@app.errorhandler(SQLAlchemyError)
def handle_sqlalchemy_error(e):
    """Handle SQLAlchemy exceptions globally."""
    logger.error("SQLAlchemy error: %s", e)
    flash("A database error occurred.", "danger")
    return redirect(url_for("list_users"))


@app.errorhandler(Exception)
def handle_unexpected_error(e):
    """Catch-all for unexpected exceptions."""
    logger.exception("Unhandled exception:")
    return render_template("500.html"), 500


# ---------------------------------------------------------------------- #
#                                main                                    #
# ---------------------------------------------------------------------- #

if __name__ == "__main__":
    app.run(debug=True)
