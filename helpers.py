import re


def is_valid_username(name: str) -> bool:
    if not name:
        return False
    if not re.search(r"[a-zA-Z]", name):
        return False
    return True


def get_user_by_id(users: list, user_id: int):
    return next((user for user in users if user.id == user_id), None)


def get_movie_by_id(movies, movie_id: int):
    return next((movie for movie in movies if movie.id == movie_id), None)


def is_valid_year(year: str) -> bool:
    if not year.isdigit():
        return False
    year_int = int(year)
    return 1880 <= year_int <= 2100


def is_valid_rating(rating: str) -> bool:
    try:
        float_rating = float(rating)
        return 0.0 <= float_rating <= 10.0
    except ValueError:
        return False


def normalize_rating(rating: str) -> float:
    return round(float(rating), 1)
