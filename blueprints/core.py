from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash

core_bp = Blueprint("core", __name__)


@core_bp.route("/")
def home():
    """
    Render the home page with basic statistics.

    :return: Rendered home page
    """
    movie_count = current_app.data_manager.count_movies()
    user_count = current_app.data_manager.count_users()
    review_count = current_app.data_manager.count_reviews()
    return render_template(
        "home.html",
        movie_count=movie_count,
        user_count=user_count,
        review_count=review_count,
    )


@core_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login with form.

    :return: Redirect or login form
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = current_app.data_manager.get_user_by_username(username)

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f"Welcome, {user.first_name}!", "success")
            next_page = request.args.get("next") or url_for("users.list_users")
            return redirect(next_page)

        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@core_bp.route("/logout")
@login_required
def logout():
    """
    Log out the current user.

    :return: Redirect to login page
    """
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("core.login"))
