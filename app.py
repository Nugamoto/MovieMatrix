import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from datamanager.sqlite_data_manager import SQLiteDataManager
from helpers import is_valid_username, get_user_by_id

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


if __name__ == "__main__":
    app.run(debug=True)
