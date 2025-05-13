"""MovieMatrix helper utilities.

This module contains pure helper functions for input validation,
normalisation and simple collection look‑ups.

All helpers are side‑effect‑free and thus easy to unit test.
"""
import re
from datetime import datetime
from typing import Optional

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")
NAME_RE = re.compile(r"^[A-Za-zÀ-ÿ' -]{2,40}$")

MIN_YEAR = 1878  # First known film
CURRENT_YEAR = datetime.now().year

MIN_RATING = 0.0
MAX_RATING = 10.0


def is_valid_username(username: str) -> bool:
    """Validate the username format (3–30 characters, alphanumerics/underscores).

    Args:
        username: The username to validate.

    Returns:
        True if valid, otherwise *False*.
    """
    return bool(USERNAME_RE.fullmatch(username))


def is_valid_email(email: str) -> bool:
    """Validate email format using a regular expression.

    Args:
        email: Email address to validate.

    Returns:
        True if valid, otherwise *False*.
    """
    return bool(EMAIL_RE.fullmatch(email))


def is_valid_name(name: str) -> bool:
    """Validate a first or last name (letters, spaces, hyphens, apostrophes).

    Args:
        name: Name to validate.

    Returns:
        True if valid, otherwise *False*.
    """
    return bool(NAME_RE.fullmatch(name.strip()))


def passwords_match(pw1: str, pw2: str) -> bool:
    """Check whether two passwords match and are non‑empty.

    Args:
        pw1: First password string.
        pw2: Second password string.

    Returns:
        True if passwords are equal and not empty, otherwise *False*.
    """
    return bool(pw1 and pw1 == pw2)


def is_valid_year(year: str) -> bool:
    """Validate that *year* is four digits between *MIN_YEAR* and *CURRENT_YEAR*.

    Args:
        year: Year string to validate.

    Returns:
        True if the year is within range, otherwise *False*.
    """
    if not year.isdigit():
        return False
    year_int = int(year)
    return MIN_YEAR <= year_int <= CURRENT_YEAR


def is_valid_rating(rating: str) -> bool:
    """Validate that *rating* is a float between *MIN_RATING* and *MAX_RATING*.

    Args:
        rating: Rating value to validate.

    Returns:
        True if rating is within range, otherwise *False*.
    """
    try:
        value = float(rating)
        return MIN_RATING <= value <= MAX_RATING
    except ValueError:
        return False


def normalize_rating(rating: str) -> float:
    """Convert *rating* string to *float* while clamping to valid boundaries.

    Args:
        rating: Rating value as string.

    Returns:
        Rating as *float* between *MIN_RATING* and *MAX_RATING*.
    """
    try:
        value = float(rating)
    except ValueError:
        value = MIN_RATING
    return max(MIN_RATING, min(value, MAX_RATING))


def get_user_by_id(users: list, user_id: int) -> Optional[object]:
    """Retrieve a *user* object by its *id* attribute.

    Args:
        users: A list of user objects.
        user_id: The ID to match.

    Returns:
        The matched user or *None* if not found.
    """
    return next((user for user in users if getattr(user, "id", None) == user_id), None)


def get_movie_by_id(movies: list, movie_id: int) -> Optional[object]:
    """Retrieve a *movie* object by its *id* attribute.

    Args:
        movies: A list of movie objects.
        movie_id: The ID to match.

    Returns:
        The matched movie or *None* if not found.
    """
    return next((movie for movie in movies if getattr(movie, "id", None) == movie_id), None)


def get_review_by_id(reviews: list, review_id: int) -> Optional[object]:
    """Retrieve a *review* object by its *id* attribute.

    Args:
        reviews: A list of review objects.
        review_id: The ID to match.

    Returns:
        The matched review or *None* if not found.
    """
    return next(
        (review for review in reviews if getattr(review, "id", None) == review_id),
        None,
    )
