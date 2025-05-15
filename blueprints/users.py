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
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash

from helpers import (
    is_valid_email,
    is_valid_username,
    is_valid_name,
    passwords_match,
)

users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.route("/")
def list_users():
    """
    Display a list of all registered users.

    :return: Rendered user list.
    """
    users = current_app.data_manager.get_all_users()
    return render_template("users.html", users=users)


@users_bp.route("/add", methods=["GET", "POST"])
def add_user():
    """
    Handle user registration via form.

    :return: Redirect to user list or render form again.
    """
    if request.method == "POST":
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

        try:
            age = int(age_raw)
        except ValueError:
            age = None

        pw_hash = generate_password_hash(password)

        try:
            user_obj = current_app.data_manager.add_user(
                username, email, first_name, pw_hash, last_name, age
            )
            if user_obj:
                flash(f"User “{username}” created.", "success")
            else:
                flash("Username or e-mail already exists.", "danger")
            return redirect(url_for("users.list_users"))
        except SQLAlchemyError as exc:
            current_app.logger.error("DB error while adding user '%s': %s", username, exc)
            flash("Database error while adding user.", "danger")
            return redirect(request.url)

    return render_template("add_user.html")


@users_bp.route("/edit/<int:user_id>", methods=["GET", "POST"])
@login_required
def update_user(user_id: int):
    """
    Edit user details.

    :param user_id: ID of user to update.
    :return: Redirect to user list or render form again.
    """
    if current_user.id != user_id:
        abort(403)

    user = current_app.data_manager.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("users.list_users"))

    if request.method == "POST":
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
            updated_user = current_app.data_manager.update_user(user_id, updated_fields)
            if updated_user:
                flash("User updated.", "success")
            else:
                flash("Update failed. User may no longer exist.", "danger")
            return redirect(url_for("users.list_users"))
        except SQLAlchemyError as exc:
            current_app.logger.error("DB error while updating user %d: %s", user_id, exc)
            flash("Database error while updating user.", "danger")
            return redirect(request.url)

    return render_template("edit_user.html", user=user)


@users_bp.route("/delete/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id: int):
    """
    Delete a user account and associated data.

    :param user_id: ID of user to delete.
    :return: Redirect to user list.
    """
    if current_user.id != user_id:
        abort(403)

    user = current_app.data_manager.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("users.list_users"))

    current_app.data_manager.delete_user(user_id)
    flash(f"User “{user.username}” deleted.", "success")
    return redirect(url_for("users.list_users"))


@users_bp.route("/<int:user_id>/change_password", methods=["GET", "POST"])
@login_required
def change_password(user_id: int):
    """
    Allow user to change their password securely.

    :param user_id: ID of user changing password.
    :return: Redirect or render password form.
    """
    if current_user.id != user_id:
        abort(403)

    user = current_app.data_manager.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("users.list_users"))

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
            flash("New password must differ from current password.", "warning")
            return redirect(request.url)

        try:
            current_app.data_manager.update_user(user_id, {
                "password_hash": generate_password_hash(new_pw)
            })
            flash("Password updated successfully.", "success")
            return redirect(url_for("users.list_users"))
        except SQLAlchemyError as exc:
            current_app.logger.error("DB error while changing password for user %d: %s", user_id, exc)
            flash("Database error while updating password.", "danger")
            return redirect(request.url)

    return render_template("change_password.html", user=user)


@users_bp.route("/<int:user_id>")
@login_required
def user_movies(user_id: int):
    """
    Show all movies associated with a user.

    :param user_id: ID of the user.
    :return: Rendered movie list.
    """
    if current_user.id != user_id:
        abort(403)

    user = current_app.data_manager.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("users.list_users"))

    movies = current_app.data_manager.get_movies_by_user(user_id)
    return render_template("user_movies.html", user=user, movies=movies)