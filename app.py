import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from clients.omdb_client import fetch_movie
from datamanager.sqlite_data_manager import SQLiteDataManager
from helpers import is_valid_username, get_user_by_id, get_movie_by_id, get_review_by_id, is_valid_year, \
    is_valid_rating, normalize_rating

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
data_manager = SQLiteDataManager("sqlite:///moviematrix.sqlite")


@app.route('/')
def home():
    return render_template("home.html")


@app.route('/users')
def list_users():
    users = data_manager.get_all_users()
    return render_template("users.html", users=users)


@app.route('/add_user', methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not is_valid_username(name):
            flash(f"Invalid username: '{name}'. Please include at least one letter.")
            return redirect(url_for("add_user"))

        try:
            data_manager.add_user(name)
        except IntegrityError:
            flash(f"Could not add user '{name}': database constraint violated.")
            return redirect(url_for("add_user"))
        except SQLAlchemyError:
            flash(f"A database error occurred while adding '{name}'.")
            return redirect(url_for("add_user"))

        flash(f"User '{name}' was added successfully!")
        return redirect(url_for("list_users"))

    return render_template("add_user.html")


@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash(f"User with ID {user_id} not found.")
        return redirect(url_for("list_users"))

    success = data_manager.delete_user(user_id)
    if success:
        flash(f"User '{user.name}' and all associated data were deleted.")
    else:
        flash(f"User could not be deleted.")

    return redirect(url_for("list_users"))


@app.route('/users/<int:user_id>')
def user_movies(user_id):
    users = data_manager.get_all_users()
    user = get_user_by_id(users, user_id)

    if user is None:
        flash(f"User with ID {user_id} not found.")
        return redirect(url_for("list_users"))

    movies = data_manager.get_user_movies(user_id)
    return render_template("user_movies.html", user=user, movies=movies)


@app.route('/users/<int:user_id>/add_movie', methods=["GET", "POST"])
def add_movie(user_id):
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash(f"User with ID {user_id} not found.")
        return redirect(url_for("list_users"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        year = request.form.get("year", "").strip()

        if not title:
            flash("Please provide a movie title.")
            return redirect(request.url)

        movie_data = fetch_movie(title, year)
        if not movie_data:
            flash(f"No movie found with title '{title}'.")
            return redirect(request.url)

        data_manager.add_movie(user_id, movie_data)
        flash(f"Movie '{movie_data['title']}' added to {user.name}'s list.")
        return redirect(url_for("user_movies", user_id=user_id))

    return render_template("add_movie.html", user=user)


@app.route('/users/<int:user_id>/update_movie/<int:movie_id>', methods=["GET", "POST"])
def update_movie(user_id, movie_id):
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash(f"User with ID {user_id} not found.")
        return redirect(url_for("list_users"))

    movies = data_manager.get_user_movies(user_id)
    movie = get_movie_by_id(movies, movie_id)
    if not movie:
        flash(f"Movie with ID {movie_id} not found.")
        return redirect(url_for("user_movies", user_id=user_id))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        director = request.form.get("director", "").strip()
        year = request.form.get("year", "").strip()
        rating = request.form.get("rating", "").strip()

        if year and not is_valid_year(year):
            flash(f"'{year}' is not a valid year.")
            return redirect(request.url)

        if rating and not is_valid_rating(rating):
            flash(f"'{rating}' is not a valid rating. Please enter a value between 0.0 and 10.0.")
            return redirect(request.url)

        updated_data = {
            "title": title,
            "director": director,
            "year": year,
            "rating": normalize_rating(rating) if rating else None
        }

        data_manager.update_movie(movie_id, updated_data)
        flash(f"Movie '{title}' was updated successfully.")
        return redirect(url_for("user_movies", user_id=user_id))  # ← hier muss es stehen

    return render_template("update_movie.html", user=user, movie=movie)


@app.route('/users/<int:user_id>/delete_movie/<int:movie_id>', methods=["POST"])
def delete_movie(user_id, movie_id):
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash(f"User with ID {user_id} not found.")
        return redirect(url_for("list_users"))

    success = data_manager.delete_movie(movie_id)
    if success:
        flash(f"Movie was deleted successfully.")
    else:
        flash(f"Movie with ID {movie_id} not found or could not be deleted.")

    return redirect(url_for("user_movies", user_id=user_id))


@app.route("/users/<int:user_id>/reviews")
def user_reviews(user_id):
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash(f"User with ID {user_id} not found.")
        return redirect(url_for("list_users"))

    reviews = data_manager.get_reviews_by_user(user_id)
    return render_template("user_reviews.html", user=user, reviews=reviews)


@app.route("/movies/<int:movie_id>/reviews/<int:user_id>")
def movie_reviews(movie_id, user_id):
    movies = data_manager.get_all_movies()
    movie = get_movie_by_id(movies, movie_id)
    if not movie:
        flash(f"Movie with ID {movie_id} not found.")
        return redirect(url_for("list_users"))

    reviews = data_manager.get_reviews_for_movie(movie_id)
    return render_template("movie_reviews.html", movie=movie, reviews=reviews, user_id=user_id)


@app.route("/users/<int:user_id>/add_review/<int:movie_id>", methods=["GET", "POST"])
def add_review(user_id, movie_id):
    user = get_user_by_id(data_manager.get_all_users(), user_id)
    if not user:
        flash(f"User with ID {user_id} not found.")
        return redirect(url_for("list_users"))

    movies = data_manager.get_user_movies(user_id)
    movie = get_movie_by_id(movies, movie_id)
    if not movie:
        flash(f"Movie with ID {movie_id} not found.")
        return redirect(url_for("user_movies", user_id=user_id))

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        user_rating = request.form.get("user_rating", "").strip()

        if not is_valid_rating(user_rating):
            flash("Invalid rating. Please enter a number between 0.0 and 10.0.")
            return redirect(request.url)

        review_data = {
            "text": text,
            "user_rating": normalize_rating(user_rating)
        }

        data_manager.add_review(user_id, movie_id, review_data)
        flash(f"Review added for '{movie.title}'.")
        return redirect(url_for("user_reviews", user_id=user_id))

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
        return redirect(url_for("user_reviews", user_id=user_id))

    movies = data_manager.get_user_movies(user_id)
    movie = get_movie_by_id(movies, review.movie_id)

    next_url = request.args.get("next")

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        user_rating = request.form.get("user_rating", "").strip()

        if not is_valid_rating(user_rating):
            flash("Invalid rating. Please enter a number between 0.0 and 10.0.")
            return redirect(request.url)

        updated_data = {
            "text": text,
            "user_rating": normalize_rating(user_rating)
        }

        data_manager.update_review(review_id, updated_data)
        flash(f"Review for '{movie.title}' updated.")

        return redirect(next_url) if next_url else redirect(url_for("user_reviews", user_id=user_id))

    return render_template("edit_review.html", user=user, movie=movie, review=review)


@app.route("/users/<int:user_id>/delete_review/<int:review_id>", methods=["POST"])
def delete_review(user_id, review_id):
    success = data_manager.delete_review(review_id)
    if success:
        flash("Review deleted successfully.")
    else:
        flash("Review could not be deleted.")
    return redirect(url_for("user_reviews", user_id=user_id))


if __name__ == "__main__":
    app.run(debug=True)
