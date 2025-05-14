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
    abort,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash

from clients.omdb_client import fetch_movie
from datamanager.sqlite_data_manager import SQLiteDataManager
from helpers import (
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

# ------------------------------ Auth ---------------------------------- #

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "warning"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id: str):
    """Return a User object for Flask-Login sessions."""
    return data_manager.get_user_by_id(int(user_id))


# ---------------------------------------------------------------------- #
#                               Routes                                   #
# ---------------------------------------------------------------------- #


@app.route("/")
def home():
    """Render landing page with basic statistics."""
    movie_count = data_manager.count_movies()
    user_count = data_manager.count_users()
    review_count = data_manager.count_reviews()
    return render_template(
        "home.html",
        movie_count=movie_count,
        user_count=user_count,
        review_count=review_count,
    )


# ------------------------------ LOGIN --------------------------------- #

@app.route("/login", methods=["GET", "POST"])
def login():
    """Render login form and authenticate user."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = data_manager.get_user_by_username(username)

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f"Welcome, {user.first_name}!", "success")
            next_page = request.args.get("next") or url_for("list_users")
            return redirect(next_page)

        flash("Invalid username or password.", "danger")
    return render_template("login.html")


# ------------------------------ LOGOUT -------------------------------- #

@app.route("/logout")
@login_required
def logout():
    """Log the current user out and redirect to login page."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ------------------------------ USERS --------------------------------- #

@app.route("/users")
def list_users():
    """List all registered users."""
    users = data_manager.get_all_users()
    return render_template("users.html", users=users)


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
        try:
            age = int(age_raw)
        except ValueError:
            age = None
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
            logger.error("DB error while adding user '%s' (email=%s): %s", username, email, exc)
            flash("Database error while adding user.", "danger")
            return redirect(request.url)

    # GET
    return render_template("add_user.html")


@app.route("/update_user/<int:user_id>", methods=["GET", "POST"])
@login_required
def update_user(user_id: int):
    """Edit a user’s account details (username, email, name, age)."""
    user = data_manager.get_user_by_id(user_id)
    if not user:
        logger.warning("User ID %d not found on route %s", user_id, request.path)
        flash("User not found.", "danger")
        return redirect(url_for("list_users"))

    if current_user.id != user_id:
        abort(403)

    if request.method == "POST":
        # --- Extract & validate ------------------------------------------------
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip() or None
        age_raw = request.form.get("age", "").strip()

        if not is_valid_username(username):
            flash("Invalid username (3–30 chars, letters, digits, _).", "danger")
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

        # --- Persist -----------------------------------------------------------
        try:
            age = int(age_raw)
        except ValueError:
            age = None
        updated_fields = {
            "username": username,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "age": age,
        }

        try:
            updated_user = data_manager.update_user(user_id, updated_fields)
            if updated_user:
                flash("User updated.", "success")
            else:
                flash("Update failed. User may no longer exist.", "danger")
            return redirect(url_for("list_users"))
        except SQLAlchemyError as exc:
            logger.error("DB error while updating user ID %d (username=%s): %s", user_id, username, exc)
            flash("Database error while updating user.", "danger")
            return redirect(request.url)

    # GET
    return render_template("edit_user.html", user=user)


@app.route("/delete_user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id: int):
    """Delete a user and cascade their movies & reviews."""
    if current_user.id != user_id:
        abort(403)

    user = data_manager.get_user_by_id(user_id)
    if not user:
        logger.warning("User ID %d not found on route %s", user_id, request.path)
        flash("User not found.", "danger")
        return redirect(url_for("list_users"))

    data_manager.delete_user(user_id)
    logger.info("User ID %d (%s) deleted by user ID %d", user.id, user.username, current_user.id)
    flash(f"User “{user.username}” deleted.", "success")
    return redirect(url_for("list_users"))


@app.route("/users/<int:user_id>/change_password", methods=["GET", "POST"])
@login_required
def change_password(user_id: int):
    """Allow a user to change their password after verifying the current one."""
    user = data_manager.get_user_by_id(user_id)
    if not user:
        logger.warning("User ID %d not found on route %s", user_id, request.path)
        flash("User not found.", "danger")
        return redirect(url_for("list_users"))

    if current_user.id != user_id:
        abort(403)

    if request.method == "POST":
        current_pw = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")

        if not check_password_hash(user.password_hash, current_pw):
            flash("Current password is incorrect.", "danger")
            return redirect(request.url)

        if not passwords_match(new_pw, confirm_pw):
            flash("New passwords do not match.", "danger")
            return redirect(request.url)

        if current_pw == new_pw:
            flash("New password must be different from current password.", "warning")
            return redirect(request.url)

        try:
            data_manager.update_user(user_id, {
                "password_hash": generate_password_hash(new_pw)
            })
            flash("Password updated successfully.", "success")
            return redirect(url_for("list_users"))
        except SQLAlchemyError as exc:
            logger.error("DB error while changing password for user ID %d (username=%s): %s", user_id, user.username,
                         exc)
            flash("Database error while updating password.", "danger")
            return redirect(request.url)

    return render_template("change_password.html", user=user)


@app.route("/users/<int:user_id>")
@login_required
def user_movies(user_id: int):
    """Show movie list for a given user."""
    if current_user.id != user_id:
        abort(403)

    user = data_manager.get_user_by_id(user_id)
    if not user:
        logger.warning("User ID %d not found on route %s", user_id, request.path)
        flash("User not found.", "danger")
        return redirect(url_for("list_users"))

    movies = data_manager.get_movies_by_user(user_id)
    return render_template("user_movies.html", user=user, movies=movies)


# ------------------------------ MOVIES -------------------------------- #

@app.route("/movies")
def all_movies():
    movies = data_manager.get_all_movies()
    return render_template("all_movies.html", movies=movies)


@app.route("/users/<int:user_id>/add_movie", methods=["GET", "POST"])
@login_required
def add_movie(user_id: int):
    """Add a movie to user's list via OMDb lookup."""
    user = data_manager.get_user_by_id(user_id)
    if not user:
        logger.warning("User ID %d not found on route %s", user_id, request.path)
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

        if year and not is_valid_year(year):
            flash("Invalid year format.", "danger")
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
@login_required
def update_movie(user_id: int, movie_id: int):
    """Edit movie meta-data (title, director, year, genre, IMDb rating)."""
    if current_user.id != user_id:
        abort(403)

    user = data_manager.get_user_by_id(user_id)
    movie = data_manager.get_movie_by_id(movie_id)
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
@login_required
def delete_movie(user_id: int, movie_id: int):
    """Remove a movie link (and possibly the movie) from a user."""
    if current_user.id != user_id:
        abort(403)

    movie = data_manager.get_movie_by_id(movie_id)
    if not movie:
        flash("Movie not found.", "danger")
        return redirect(url_for("user_movies", user_id=user_id))

    data_manager.delete_movie(movie_id)
    flash("Movie deleted.", "success")
    return redirect(url_for("user_movies", user_id=user_id))


# ------------------------------ REVIEWS ------------------------------ #

@app.route("/users/<int:user_id>/reviews")
@login_required
def user_reviews(user_id: int):
    """Display all reviews authored by a user."""
    if current_user.id != user_id:
        abort(403)

    user = data_manager.get_user_by_id(user_id)
    if not user:
        logger.warning("User ID %d not found on route %s", user_id, request.path)
        flash(f"User with ID {user_id} not found.")
        logger.warning("User ID %d not found when accessing reviews (path: %s)", user_id, request.path)
        return redirect(url_for("list_users"))

    reviews = data_manager.get_reviews_by_user(user_id)
    next_url = request.args.get("next") or request.referrer or url_for("user_movies", user_id=user_id)
    return render_template("user_reviews.html", user=user, reviews=reviews, next=next_url)


@app.route("/users/<int:user_id>/review/<int:review_id>")
def review_detail(user_id: int, review_id: int):
    review = data_manager.get_review_detail(review_id)
    if not review or review.user_id != user_id:
        logger.warning("Review ID %d not found or does not belong to user ID %d", review_id, user_id)
        flash("Review not found.", "warning")
        return redirect(url_for("user_reviews", user_id=user_id))

    movie = review.movie
    is_owner = current_user.is_authenticated and current_user.id == user_id
    return render_template(
        "review_detail.html",
        review=review,
        movie=movie,
        is_owner=is_owner,
    )


@app.route("/movies/<int:movie_id>/reviews")
def movie_reviews(movie_id: int):
    """List reviews for a movie; optional user_id enables 'Add Review' button."""
    movie = data_manager.get_movie_by_id(movie_id)
    if not movie:
        flash(f"Movie with ID {movie_id} not found.")
        logger.warning("Movie ID %d not found when accessing reviews (path: %s)", movie_id, request.path)
        return redirect(url_for("list_users"))

    reviews = data_manager.get_reviews_for_movie(movie_id)
    next_url = request.args.get("next") or request.referrer or url_for("all_movies")
    return render_template(
        "movie_reviews.html",
        movie=movie,
        reviews=reviews,
        next_url=next_url,
    )


@app.route("/users/<int:user_id>/movies/<int:movie_id>/add_review", methods=["GET", "POST"])
@login_required
def add_review(user_id: int, movie_id: int):
    """Add a new review (title, text, rating) for a movie."""
    if current_user.id != user_id:
        abort(403)

    user = data_manager.get_user_by_id(user_id)
    movie = data_manager.get_movie_by_id(movie_id)
    if not user or not movie:
        logger.warning("User ID %d not found on route %s", user_id, request.path)
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
@login_required
def edit_review(user_id: int, review_id: int):
    """Edit a user’s review (title, text, rating)."""
    if current_user.id != user_id:
        abort(403)

    user = data_manager.get_user_by_id(user_id)
    review = data_manager.get_review_by_id(review_id)
    if not user or not review:
        logger.warning("User ID %d not found on route %s", user_id, request.path)
        flash("User or review not found.", "danger")
        return redirect(url_for("list_users"))

    movie = data_manager.get_movie_by_id(review.movie_id)
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
@login_required
def delete_review(user_id: int, review_id: int):
    """Delete a review authored by a user."""
    if current_user.id != user_id:
        abort(403)

    review = data_manager.get_review_by_id(review_id)
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


@app.errorhandler(403)
def forbidden(e):
    """Handle 403 Forbidden errors with a redirect and flash message."""
    logger.warning("403 error: Forbidden access to %s (user_id=%s)", request.path,
                   getattr(current_user, "id", "anonymous"))
    flash("You are not allowed to access this resource.", "warning")
    return redirect(url_for("list_users"))


@app.errorhandler(500)
def internal_server_error(e):
    """Render custom 500 page."""
    logger.exception("500 error occurred: %s", str(e))
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
    logger.exception("Unhandled exception at %s", request.path)
    return render_template("500.html"), 500


# ---------------------------------------------------------------------- #
#                                main                                    #
# ---------------------------------------------------------------------- #

if __name__ == "__main__":
    app.run(debug=True)
