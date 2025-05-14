# blueprints/reviews.py
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

from helpers import is_valid_rating, normalize_rating

reviews_bp = Blueprint("reviews", __name__, url_prefix="/reviews")


@reviews_bp.route("/user/<int:user_id>")
@login_required
def user_reviews(user_id: int):
    """
    Display all reviews authored by a specific user.

    :param user_id: ID of the user
    :return: Rendered template with reviews
    """
    if current_user.id != user_id:
        abort(403)

    user = current_app.data_manager.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("users.list_users"))

    reviews = current_app.data_manager.get_reviews_by_user(user_id)
    next_url = request.args.get("next") or request.referrer or url_for("users.user_movies", user_id=user_id)
    return render_template("user_reviews.html", user=user, reviews=reviews, next=next_url)


@reviews_bp.route("/user/<int:user_id>/review/<int:review_id>")
def review_detail(user_id: int, review_id: int):
    """
    Show detailed view of a review.

    :param user_id: ID of the user
    :param review_id: ID of the review
    :return: Rendered review detail template
    """
    review = current_app.data_manager.get_review_detail(review_id)
    if not review or review.user_id != user_id:
        flash("Review not found.", "warning")
        return redirect(url_for("reviews.user_reviews", user_id=user_id))

    movie = review.movie
    is_owner = current_user.is_authenticated and current_user.id == user_id
    return render_template("review_detail.html", review=review, movie=movie, is_owner=is_owner)


@reviews_bp.route("/movie/<int:movie_id>")
def movie_reviews(movie_id: int):
    """
    List all reviews for a specific movie.

    :param movie_id: ID of the movie
    :return: Rendered review list template
    """
    movie = current_app.data_manager.get_movie_by_id(movie_id)
    if not movie:
        flash("Movie not found.", "danger")
        return redirect(url_for("users.list_users"))

    reviews = current_app.data_manager.get_reviews_for_movie(movie_id)
    next_url = request.args.get("next") or request.referrer or url_for("movies.list_movies")
    return render_template("movie_reviews.html", movie=movie, reviews=reviews, next_url=next_url)


@reviews_bp.route("/user/<int:user_id>/movie/<int:movie_id>/add", methods=["GET", "POST"])
@login_required
def add_review(user_id: int, movie_id: int):
    """
    Add a new review for a movie by a user.

    :param user_id: ID of the user
    :param movie_id: ID of the movie
    :return: Redirect or rendered form
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
        text = request.form.get("text", "").strip()
        rating = request.form.get("user_rating", "").strip()

        if not title or not text:
            flash("Title and text required.", "danger")
            return redirect(request.url)
        if not is_valid_rating(rating):
            flash("Rating must be 0-10.", "danger")
            return redirect(request.url)

        current_app.data_manager.add_review(
            user_id,
            movie_id,
            {"title": title, "text": text, "user_rating": normalize_rating(rating)},
        )
        flash("Review added.", "success")
        return redirect(url_for("reviews.movie_reviews", movie_id=movie_id, user_id=user_id))

    return render_template("add_review.html", user=user, movie=movie)


@reviews_bp.route("/user/<int:user_id>/edit/<int:review_id>", methods=["GET", "POST"])
@login_required
def edit_review(user_id: int, review_id: int):
    """
    Edit an existing review.

    :param user_id: ID of the user
    :param review_id: ID of the review
    :return: Redirect or rendered form
    """
    if current_user.id != user_id:
        abort(403)

    user = current_app.data_manager.get_user_by_id(user_id)
    review = current_app.data_manager.get_review_by_id(review_id)
    if not user or not review:
        flash("User or review not found.", "danger")
        return redirect(url_for("users.list_users"))

    movie = current_app.data_manager.get_movie_by_id(review.movie_id)
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

        current_app.data_manager.update_review(
            review_id,
            {"title": title, "text": text, "user_rating": normalize_rating(rating)},
        )
        flash("Review updated.", "success")
        return redirect(next_url) if next_url else redirect(url_for("reviews.user_reviews", user_id=user_id))

    return render_template("edit_review.html", user=user, movie=movie, review=review)


@reviews_bp.route("/user/<int:user_id>/delete/<int:review_id>", methods=["POST"])
@login_required
def delete_review(user_id: int, review_id: int):
    """
    Delete a review authored by a user.

    :param user_id: ID of the user
    :param review_id: ID of the review
    :return: Redirect to user's review list
    """
    if current_user.id != user_id:
        abort(403)

    review = current_app.data_manager.get_review_by_id(review_id)
    if not review:
        flash("Review not found.", "danger")
        return redirect(url_for("reviews.user_reviews", user_id=user_id))

    current_app.data_manager.delete_review(review_id)
    flash("Review deleted.", "success")
    return redirect(url_for("reviews.user_reviews", user_id=user_id))
