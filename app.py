import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from clients.omdb_client import fetch_movie
from datamanager.sqlite_data_manager import SQLiteDataManager
from helpers import is_valid_username, get_user_by_id, is_valid_year, is_valid_rating, normalize_rating

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
    movie = next((movie for movie in movies if movie.id == movie_id), None)
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


if __name__ == "__main__":
    app.run(debug=True)
