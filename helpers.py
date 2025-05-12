import re
from datetime import datetime

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")
NAME_RE = re.compile(r"^[A-Za-zÀ-ÿ' -]{2,40}$")

MIN_YEAR = 1878  # First known film
CURRENT_YEAR = datetime.now().year

MIN_RATING = 0.0
MAX_RATING = 10.0


def is_valid_username(username: str) -> bool:
    return bool(USERNAME_RE.fullmatch(username))


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.fullmatch(email))


def is_valid_name(name: str) -> bool:
    return bool(NAME_RE.fullmatch(name.strip()))


def passwords_match(pw1: str, pw2: str) -> bool:
    return pw1 and pw1 == pw2


def is_valid_year(year: str) -> bool:
    """
    Validate that the year is numeric and within a realistic movie year range.

    Args:
        year (str): The year to validate.

    Returns:
        bool: True if year is between MIN_YEAR and CURRENT_YEAR, False otherwise.
    """
    if not year.isdigit():
        return False
    year_int = int(year)
    return MIN_YEAR <= year_int <= CURRENT_YEAR


def is_valid_rating(rating: str) -> bool:
    """
    Validate that the rating is a float and between MIN_RATING and MAX_RATING.

    Args:
        rating (str): The rating value to validate.

    Returns:
        bool: True if the rating is within range, False otherwise.
    """
    try:
        value = float(rating)
        return MIN_RATING <= value <= MAX_RATING
    except ValueError:
        return False


def normalize_rating(rating: str) -> float:
    """
    Convert a string rating to a float rounded to one decimal place.

    Args:
        rating (str): The rating string.

    Returns:
        float: The normalized rating.
    """
    return round(float(rating), 1)


def get_user_by_id(users: list, user_id: int):
    """
    Retrieve a user object by its ID.

    Args:
        users (list): List of user objects.
        user_id (int): The ID to match.

    Returns:
        User | None: The matched user or None if not found.
    """
    return next((user for user in users if user.id == user_id), None)


def get_movie_by_id(movies: list, movie_id: int):
    """
    Retrieve a movie object by its ID.

    Args:
        movies (list): List of movie objects.
        movie_id (int): The ID to match.

    Returns:
        Movie | None: The matched movie or None if not found.
    """
    return next((movie for movie in movies if movie.id == movie_id), None)


def get_review_by_id(reviews: list, review_id: int):
    """
    Retrieve a review object by its ID.

    Args:
        reviews (list): List of review objects.
        review_id (int): The ID to match.

    Returns:
        Review | None: The matched review or None if not found.
    """
    return next((review for review in reviews if review.id == review_id), None)
