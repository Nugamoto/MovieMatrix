import os

from dotenv import load_dotenv
from flask import Flask, render_template

from datamanager.sqlite_data_manager import SQLiteDataManager

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


if __name__ == "__main__":
    app.run(debug=True)
