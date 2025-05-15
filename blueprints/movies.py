from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    current_app,
)
from flask_login import login_required, current_user

from clients.omdb_client import fetch_movie
from utils.helpers import is_valid_year, is_valid_rating, normalize_rating

movies_bp = Blueprint("movies", __name__, url_prefix="/movies")


@movies_bp.route("/")
def list_movies():
    """
    Display a list of all movies.

    :return: Rendered template with movie list.
    """
    movies = current_app.data_manager.get_all_movies()
    return render_template("all_movies.html", movies=movies)


@movies_bp.route("/add/<int:user_id>", methods=["GET", "POST"])
@login_required
def add_movie(user_id: int):
    """
    Add a movie to a user's list by performing an OMDb lookup.

    :param user_id: ID of the user adding the movie.
    :return: Redirect to the user's movie list or show form again.
    """
    if current_user.id != user_id:
        abort(403)

    user = current_app.data_manager.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("users.list_users"))

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

        current_app.data_manager.add_movie(
            user_id, movie_data, planned, watched, favorite
        )
        flash(f"Movie “{movie_data['title']}” added.", "success")
        return redirect(url_for("users.user_movies", user_id=user_id))

    return render_template("add_movie.html", user=user)


@movies_bp.route("/edit/<int:user_id>/<int:movie_id>", methods=["GET", "POST"])
@login_required
def update_movie(user_id: int, movie_id: int):
    """
    Edit metadata for a specific movie.

    :param user_id: ID of the user editing the movie.
    :param movie_id: ID of the movie to edit.
    :return: Redirect to user's movie list or render form again.
    """
    if current_user.id != user_id:
        abort(403)

    user = current_app.data_manager.get_user_by_id(user_id)
    movie = current_app.data_manager.get_movie_by_id(movie_id)
    if not user or not movie:
        flash("User or movie not found.", "danger")
        return redirect(url_for("users.list_users"))

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
        current_app.data_manager.update_movie(movie_id, updated_data)
        flash("Movie updated.", "success")
        return redirect(url_for("users.user_movies", user_id=user_id))

    return render_template("edit_movie.html", user=user, movie=movie)


@movies_bp.route("/delete/<int:user_id>/<int:movie_id>", methods=["POST"])
@login_required
def delete_movie(user_id: int, movie_id: int):
    """
    Delete a movie from a user's collection.

    :param user_id: ID of the user.
    :param movie_id: ID of the movie to delete.
    :return: Redirect to user's movie list.
    """
    if current_user.id != user_id:
        abort(403)

    movie = current_app.data_manager.get_movie_by_id(movie_id)
    if not movie:
        flash("Movie not found.", "danger")
        return redirect(url_for("users.user_movies", user_id=user_id))

    current_app.data_manager.delete_movie(movie_id)
    flash("Movie deleted.", "success")
    return redirect(url_for("users.user_movies", user_id=user_id))
