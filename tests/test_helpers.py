import pytest

from helpers import (
    is_valid_username,
    get_user_by_id,
    get_movie_by_id,
    get_review_by_id,
    is_valid_year,
    is_valid_rating,
    normalize_rating
)


@pytest.mark.parametrize("name,expected", [
    ("JohnDoe", True),
    ("", False),
    ("   ", False),
    ("###", False),
    ("1234", False),
    ("valid_user123", True),
])
def test_is_valid_username(name, expected):
    """Test is_valid_username with various valid and invalid inputs."""
    assert is_valid_username(name) is expected


@pytest.mark.parametrize("users,user_id,expected_name", [
    ([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}], 1, "Alice"),
    ([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}], 2, "Bob"),
    ([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}], 3, None),
])
def test_get_user_by_id(users, user_id, expected_name):
    """Test get_user_by_id returns correct user or None."""
    user_objs = [type("User", (), u)() for u in users]
    result = get_user_by_id(user_objs, user_id)
    if expected_name is None:
        assert result is None
    else:
        assert result.name == expected_name


@pytest.mark.parametrize("movies,movie_id,expected_title", [
    ([{"id": 10, "title": "Matrix"}, {"id": 20, "title": "Inception"}], 10, "Matrix"),
    ([{"id": 10, "title": "Matrix"}, {"id": 20, "title": "Inception"}], 20, "Inception"),
    ([{"id": 10, "title": "Matrix"}], 30, None),
])
def test_get_movie_by_id(movies, movie_id, expected_title):
    """Test get_movie_by_id returns correct movie or None."""
    movie_objs = [type("Movie", (), m)() for m in movies]
    result = get_movie_by_id(movie_objs, movie_id)
    if expected_title is None:
        assert result is None
    else:
        assert result.title == expected_title


@pytest.mark.parametrize("reviews,review_id,expected_text", [
    ([{"id": 1, "text": "Great!"}, {"id": 2, "text": "Bad!"}], 1, "Great!"),
    ([{"id": 1, "text": "Great!"}, {"id": 2, "text": "Bad!"}], 2, "Bad!"),
    ([{"id": 1, "text": "Great!"}], 5, None),
])
def test_get_review_by_id(reviews, review_id, expected_text):
    """Test get_review_by_id returns correct review or None."""
    review_objs = [type("Review", (), r)() for r in reviews]
    result = get_review_by_id(review_objs, review_id)
    if expected_text is None:
        assert result is None
    else:
        assert result.text == expected_text


@pytest.mark.parametrize("year_str,expected", [
    ("1999", True),
    ("2025", True),
    ("1877", False),
    ("2101", False),
    ("abcd", False),
    ("", False),
])
def test_is_valid_year(year_str, expected):
    """Test is_valid_year for valid format and reasonable range."""
    assert is_valid_year(year_str) is expected


@pytest.mark.parametrize("value,expected", [
    ("0", True),
    ("5", True),
    ("9.9", True),
    ("10.0", True),
    ("10.1", False),
    ("-1", False),
    ("abc", False),
    ("", False),
])
def test_is_valid_rating(value, expected):
    """Test is_valid_rating for numeric input and allowed range."""
    assert is_valid_rating(value) is expected


@pytest.mark.parametrize("value,expected", [
    ("5.567", 5.6),
    ("8.94", 8.9),
    ("0", 0.0),
    ("10", 10.0),
])
def test_normalize_rating(value, expected):
    """Test normalize_rating rounds input to 1 decimal place as float."""
    assert normalize_rating(value) == expected
